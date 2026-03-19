from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import get_db_connection
from datetime import datetime

bp = Blueprint('content', __name__, url_prefix='/content')

@bp.route('/')
def index():
    conn = get_db_connection()
    contents = conn.execute('SELECT * FROM email_contents ORDER BY updated_at DESC').fetchall()
    conn.close()
    return render_template('content/index.html', contents=contents)

@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not title or not body:
            flash('请填写标题和内容', 'error')
            return render_template('content/form.html', content=None)

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO email_contents (title, body, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (title, body, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()

        flash('邮件内容已创建', 'success')
        return redirect(url_for('content.index'))

    return render_template('content/form.html', content=None)

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    content = conn.execute('SELECT * FROM email_contents WHERE id = ?', (id,)).fetchone()

    if not content:
        conn.close()
        flash('邮件内容不存在', 'error')
        return redirect(url_for('content.index'))

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not title or not body:
            flash('请填写标题和内容', 'error')
            conn.close()
            return render_template('content/form.html', content=content)

        conn.execute('''
            UPDATE email_contents
            SET title = ?, body = ?, updated_at = ?
            WHERE id = ?
        ''', (title, body, datetime.now(), id))
        conn.commit()
        conn.close()

        flash('邮件内容已更新', 'success')
        return redirect(url_for('content.index'))

    conn.close()
    return render_template('content/form.html', content=content)

@bp.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM email_contents WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('邮件内容已删除', 'success')
    return redirect(url_for('content.index'))

def get_content_by_id(id):
    conn = get_db_connection()
    content = conn.execute('SELECT * FROM email_contents WHERE id = ?', (id,)).fetchone()
    conn.close()
    return content

def get_all_contents():
    conn = get_db_connection()
    contents = conn.execute('SELECT * FROM email_contents ORDER BY updated_at DESC').fetchall()
    conn.close()
    return contents
