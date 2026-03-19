from flask import Blueprint, render_template, request
from app import get_db_connection

bp = Blueprint('logs', __name__, url_prefix='/logs')

@bp.route('/')
def index():
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    
    where_clauses = []
    params = []
    
    if status_filter:
        where_clauses.append('l.status = ?')
        params.append(status_filter)
    
    if search:
        where_clauses.append('l.subject LIKE ?')
        params.append(f'%{search}%')
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    total = conn.execute(f'SELECT COUNT(*) as count FROM email_logs l WHERE {where_sql}', params).fetchone()['count']
    
    logs = conn.execute(f'''
        SELECT l.*, s.name as smtp_name, c.title as content_title
        FROM email_logs l
        LEFT JOIN smtp_settings s ON l.smtp_config_id = s.id
        LEFT JOIN email_contents c ON l.content_id = c.id
        WHERE {where_sql}
        ORDER BY l.sent_at DESC
        LIMIT ? OFFSET ?
    ''', params + [per_page, offset]).fetchall()
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('logs/index.html', 
                           logs=logs, 
                           page=page, 
                           total_pages=total_pages,
                           status_filter=status_filter,
                           search=search)

@bp.route('/<int:id>')
def detail(id):
    conn = get_db_connection()
    
    log = conn.execute('''
        SELECT l.*, s.name as smtp_name, s.smtp_host, c.title as content_title, c.body as content_body
        FROM email_logs l
        LEFT JOIN smtp_settings s ON l.smtp_config_id = s.id
        LEFT JOIN email_contents c ON l.content_id = c.id
        WHERE l.id = ?
    ''', (id,)).fetchone()
    
    if not log:
        conn.close()
        return '日志不存在', 404
    
    customers = conn.execute('''
        SELECT c.*, l.sent_at as email_sent_at
        FROM customers c
        WHERE c.last_email_sent_at IS NOT NULL
        AND c.last_email_sent_at >= ?
        AND c.last_email_sent_at <= datetime(?, '+1 hour')
        ORDER BY c.last_email_sent_at DESC
        LIMIT 100
    ''', (log['sent_at'], log['sent_at'])).fetchall()
    
    conn.close()
    
    return render_template('logs/detail.html', log=log, customers=customers)
