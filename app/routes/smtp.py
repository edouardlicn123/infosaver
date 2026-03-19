import smtplib
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import get_db_connection

bp = Blueprint('smtp', __name__, url_prefix='/smtp')

@bp.route('/')
def index():
    conn = get_db_connection()
    configs = conn.execute('SELECT * FROM smtp_settings ORDER BY is_default DESC, created_at DESC').fetchall()
    conn.close()
    return render_template('smtp/index.html', configs=configs)

@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        smtp_host = request.form['smtp_host']
        smtp_port = int(request.form['smtp_port'])
        smtp_user = request.form['smtp_user']
        smtp_password = request.form['smtp_password']
        use_tls = 1 if request.form.get('use_tls') else 0
        sender_name = request.form.get('sender_name', '')
        sender_email = request.form['sender_email']
        is_default = 1 if request.form.get('is_default') else 0

        if not name or not smtp_host or not smtp_user or not smtp_password or not sender_email:
            flash('请填写所有必填字段', 'error')
            return render_template('smtp/form.html', config=None)

        conn = get_db_connection()
        if is_default:
            conn.execute('UPDATE smtp_settings SET is_default = 0')
        conn.execute('''
            INSERT INTO smtp_settings (name, smtp_host, smtp_port, smtp_user, smtp_password, use_tls, sender_name, sender_email, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, smtp_host, smtp_port, smtp_user, smtp_password, use_tls, sender_name, sender_email, is_default))
        conn.commit()
        conn.close()

        flash('SMTP配置已添加', 'success')
        return redirect(url_for('smtp.index'))

    return render_template('smtp/form.html', config=None)

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM smtp_settings WHERE id = ?', (id,)).fetchone()

    if not config:
        conn.close()
        flash('配置不存在', 'error')
        return redirect(url_for('smtp.index'))

    if request.method == 'POST':
        name = request.form['name']
        smtp_host = request.form['smtp_host']
        smtp_port = int(request.form['smtp_port'])
        smtp_user = request.form['smtp_user']
        smtp_password = request.form['smtp_password']
        use_tls = 1 if request.form.get('use_tls') else 0
        sender_name = request.form.get('sender_name', '')
        sender_email = request.form['sender_email']
        is_default = 1 if request.form.get('is_default') else 0

        if not name or not smtp_host or not smtp_user or not smtp_password or not sender_email:
            flash('请填写所有必填字段', 'error')
            conn.close()
            return render_template('smtp/form.html', config=config)

        if is_default:
            conn.execute('UPDATE smtp_settings SET is_default = 0')

        conn.execute('''
            UPDATE smtp_settings
            SET name = ?, smtp_host = ?, smtp_port = ?, smtp_user = ?, smtp_password = ?,
                use_tls = ?, sender_name = ?, sender_email = ?, is_default = ?
            WHERE id = ?
        ''', (name, smtp_host, smtp_port, smtp_user, smtp_password, use_tls, sender_name, sender_email, is_default, id))
        conn.commit()
        conn.close()

        flash('SMTP配置已更新', 'success')
        return redirect(url_for('smtp.index'))

    conn.close()
    return render_template('smtp/form.html', config=config)

@bp.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM smtp_settings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('SMTP配置已删除', 'success')
    return redirect(url_for('smtp.index'))

@bp.route('/<int:id>/test', methods=('POST',))
def test(id):
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM smtp_settings WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not config:
        flash('配置不存在', 'error')
        return redirect(url_for('smtp.index'))

    try:
        if config['use_tls'] == 2:
            with smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port'], timeout=10) as server:
                server.login(config['smtp_user'], config['smtp_password'])
        else:
            server = smtplib.SMTP(config['smtp_host'], config['smtp_port'], timeout=10)
            if config['use_tls']:
                server.starttls()
            server.login(config['smtp_user'], config['smtp_password'])
            server.quit()
        flash('连接测试成功！', 'success')
    except Exception as e:
        flash(f'连接测试失败: {str(e)}', 'error')

    return redirect(url_for('smtp.index'))

def get_default_smtp():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM smtp_settings WHERE is_default = 1').fetchone()
    if not config:
        config = conn.execute('SELECT * FROM smtp_settings ORDER BY created_at DESC').fetchone()
    conn.close()
    return config
