import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, make_response, flash
from app import get_db_connection

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route('', methods=['GET'])
def index():
    return render_template('export/index.html')

@bp.route('/xls', methods=['GET'])
def export_xls():
    import pandas as pd
    
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers ORDER BY created_at DESC').fetchall()
    conn.close()
    
    data = []
    for c in customers:
        data.append({
            '姓名': c['name'],
            '职位': c['position'],
            '邮箱1': c['email1'],
            '邮箱2': c['email2'],
            '电话1': c['phone1'],
            '电话2': c['phone2'],
            '企业': c['company'],
            '国籍': c['nationality'],
            '来源': c['source']
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='客户信息')
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=customers.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return response

@bp.route('/csv', methods=['GET'])
def export_csv():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers ORDER BY created_at DESC').fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['姓名', '职位', '邮箱1', '邮箱2', '电话1', '电话2', '企业', '国籍', '来源'])
    
    for c in customers:
        writer.writerow([
            c['name'], c['position'], c['email1'], c['email2'],
            c['phone1'], c['phone2'], c['company'], c['nationality'], c['source']
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=customers.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

@bp.route('/emails', methods=['GET'])
def export_emails():
    conn = get_db_connection()
    customers = conn.execute('SELECT email1 FROM customers WHERE email1 != "" ORDER BY email1').fetchall()
    conn.close()
    
    emails = [c['email1'] for c in customers]
    
    output = '\n'.join(emails)
    
    response = make_response(output)
    response.headers['Content-Disposition'] = 'attachment; filename=emails.txt'
    response.headers['Content-Type'] = 'text/plain'
    
    return response
