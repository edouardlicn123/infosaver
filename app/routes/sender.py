import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import get_db_connection
from datetime import datetime
from app.routes.smtp import get_default_smtp
from app.routes.content import get_content_by_id, get_all_contents

bp = Blueprint('sender', __name__, url_prefix='/sender')

@bp.route('/')
def index():
    contents = get_all_contents()
    smtp_config = get_default_smtp()
    
    conn = get_db_connection()
    smtp_configs = conn.execute('SELECT * FROM smtp_settings ORDER BY is_default DESC, created_at DESC').fetchall()
    customers = conn.execute('''
        SELECT * FROM customers 
        WHERE email1 IS NOT NULL AND email1 != ''
        ORDER BY id DESC
        LIMIT 50
    ''').fetchall()
    
    nationalities = conn.execute('SELECT DISTINCT nationality FROM customers WHERE nationality IS NOT NULL AND nationality != ""').fetchall()
    companies = conn.execute('SELECT DISTINCT company FROM customers WHERE company IS NOT NULL AND company != "" LIMIT 50').fetchall()
    conn.close()
    
    return render_template('sender/index.html', 
                           contents=contents, 
                           smtp_config=smtp_config,
                           smtp_configs=smtp_configs,
                           customers=customers,
                           nationalities=nationalities,
                           companies=companies)

@bp.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '')
    nationality = request.args.get('nationality', '')
    company = request.args.get('company', '')
    
    conn = get_db_connection()
    query = 'SELECT * FROM customers WHERE email1 IS NOT NULL AND email1 != ""'
    params = []
    
    if keyword:
        query += ' AND (name LIKE ? OR email1 LIKE ? OR company LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    if nationality:
        query += ' AND nationality = ?'
        params.append(nationality)
    if company:
        query += ' AND company = ?'
        params.append(company)
    
    query += ' ORDER BY id DESC LIMIT 100'
    
    customers = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in customers])

@bp.route('/confirm', methods=['POST'])
def confirm():
    content_id = request.form.get('content_id')
    smtp_id = request.form.get('smtp_id')
    interval = int(request.form.get('interval', 30))
    customer_ids = request.form.getlist('customer_ids')
    
    if not content_id:
        flash('请选择邮件内容', 'error')
        return redirect(url_for('sender.index'))
    
    if not customer_ids:
        flash('请选择收件人', 'error')
        return redirect(url_for('sender.index'))
    
    content = get_content_by_id(content_id)
    if not content:
        flash('邮件内容不存在', 'error')
        return redirect(url_for('sender.index'))
    
    conn = get_db_connection()
    customers = conn.execute(f'SELECT * FROM customers WHERE id IN ({",".join("?" * len(customer_ids))})', customer_ids).fetchall()
    conn.close()
    
    smtp_config = None
    if smtp_id:
        conn = get_db_connection()
        smtp_config = conn.execute('SELECT * FROM smtp_settings WHERE id = ?', (smtp_id,)).fetchone()
        conn.close()
    if not smtp_config:
        smtp_config = get_default_smtp()
    
    session['sender_content_id'] = content_id
    session['sender_smtp_id'] = smtp_config['id'] if smtp_config else None
    session['sender_interval'] = interval
    session['sender_customer_ids'] = customer_ids
    
    return render_template('sender/confirm.html',
                           content=content,
                           smtp_config=smtp_config,
                           customers=customers,
                           interval=interval)

@bp.route('/send', methods=['POST'])
def send():
    content_id = session.get('sender_content_id')
    smtp_id = session.get('sender_smtp_id')
    interval = session.get('sender_interval', 30)
    customer_ids = session.get('sender_customer_ids', [])
    
    if not content_id or not customer_ids:
        flash('发送参数不完整，请重新开始', 'error')
        return redirect(url_for('sender.index'))
    
    content = get_content_by_id(content_id)
    if not content:
        flash('邮件内容不存在', 'error')
        return redirect(url_for('sender.index'))
    
    conn = get_db_connection()
    smtp_config = conn.execute('SELECT * FROM smtp_settings WHERE id = ?', (smtp_id,)).fetchone() if smtp_id else None
    if not smtp_config:
        smtp_config = get_default_smtp()
    
    if not smtp_config:
        flash('没有可用的SMTP配置', 'error')
        return redirect(url_for('sender.index'))
    
    customers = conn.execute(f'SELECT * FROM customers WHERE id IN ({",".join("?" * len(customer_ids))})', customer_ids).fetchall()
    conn.close()
    
    success_count = 0
    fail_count = 0
    errors = []
    
    for i, customer in enumerate(customers):
        try:
            subject = replace_variables(content['title'], customer)
            body = replace_variables(content['body'], customer)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{smtp_config['sender_name'] or ''} <{smtp_config['sender_email']}>".strip()
            msg['To'] = customer['email1']
            
            if '<html>' in body.lower() or '<p>' in body.lower() or '<div>' in body.lower():
                html_part = MIMEText(body, 'html', 'utf-8')
            else:
                html_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(html_part)
            
            if smtp_config['use_tls'] == 2:
                with smtplib.SMTP_SSL(smtp_config['smtp_host'], smtp_config['smtp_port'], timeout=30) as server:
                    server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port'], timeout=30) as server:
                    if smtp_config['use_tls']:
                        server.starttls()
                    server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
                    server.send_message(msg)
            
            conn = get_db_connection()
            conn.execute('UPDATE customers SET last_email_sent_at = ? WHERE id = ?', (datetime.now(), customer['id']))
            conn.commit()
            conn.close()
            
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            errors.append(f"{customer['email1']}: {str(e)}")
        
        if i < len(customers) - 1:
            time.sleep(interval)
    
    log_id = save_email_log(content_id, smtp_config['id'] if smtp_config else None, 
                            content['title'], len(customers), success_count, fail_count,
                            'success' if fail_count == 0 else 'partial', '; '.join(errors[:10]))
    
    for key in ['sender_content_id', 'sender_smtp_id', 'sender_interval', 'sender_customer_ids']:
        session.pop(key, None)
    
    return render_template('sender/result.html', 
                           success_count=success_count, 
                           fail_count=fail_count,
                           total=len(customers),
                           log_id=log_id,
                           errors=errors)

def replace_variables(text, customer):
    replacements = {
        '{name}': customer['name'] or '',
        '{email}': customer['email1'] or '',
        '{company}': customer['company'] or '',
        '{position}': customer['position'] or ''
    }
    result = text
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result

def save_email_log(content_id, smtp_config_id, subject, recipient_count, success_count, fail_count, status, error_message):
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO email_logs (content_id, smtp_config_id, subject, recipient_count, success_count, fail_count, status, error_message, sent_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (content_id, smtp_config_id, subject, recipient_count, success_count, fail_count, status, error_message, datetime.now()))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id
