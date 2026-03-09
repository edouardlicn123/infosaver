from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app import get_db_connection

bp = Blueprint('customers', __name__, url_prefix='/customers')

@bp.route('', methods=['GET'])
def list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    
    if search:
        query = '''
            SELECT * FROM customers 
            WHERE name LIKE ? OR email1 LIKE ? OR company LIKE ?
            ORDER BY created_at DESC
        '''
        search_pattern = f'%{search}%'
        customers = conn.execute(query, (search_pattern, search_pattern, search_pattern)).fetchall()
    else:
        customers = conn.execute('SELECT * FROM customers ORDER BY created_at DESC').fetchall()
    
    conn.close()
    
    total = len(customers)
    start = (page - 1) * per_page
    end = start + per_page
    customers_page = customers[start:end]
    
    return render_template('customers/list.html', 
                         customers=customers_page, 
                         page=page, 
                         total=total,
                         per_page=per_page,
                         search=search)

@bp.route('/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        position = request.form.get('position', '')
        email1 = request.form.get('email1', '')
        email2 = request.form.get('email2', '')
        phone1 = request.form.get('phone1', '')
        phone2 = request.form.get('phone2', '')
        company = request.form.get('company', '')
        nationality = request.form.get('nationality', '')
        
        conn.execute('''
            UPDATE customers 
            SET name=?, position=?, email1=?, email2=?, phone1=?, phone2=?, company=?, nationality=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (name, position, email1, email2, phone1, phone2, company, nationality, id))
        conn.commit()
        conn.close()
        
        flash('客户信息已更新', 'success')
        return redirect(url_for('customers.list'))
    
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    return render_template('customers/edit.html', customer=customer)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM customers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('客户记录已删除', 'success')
    return redirect(url_for('customers.list'))
