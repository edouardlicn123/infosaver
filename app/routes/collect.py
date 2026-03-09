import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

bp = Blueprint('collect', __name__, url_prefix='/collect')

def clean_source(text):
    if not text:
        return ''
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    words = text.split(' ')
    unique_words = []
    for w in words:
        if not unique_words or w != unique_words[-1]:
            unique_words.append(w)
    text = ' '.join(unique_words)
    
    return text.strip()

def clean_name_position(text):
    if not text:
        return ''
    text = text.strip()
    
    pattern = r'([A-Z][a-z]+|[A-Z]+[a-z]*|[a-z]+)'
    parts = re.findall(pattern, text)
    
    n = len(parts)
    if n >= 6:
        for size in range(2, n // 2 + 1):
            first = parts[:size]
            second = parts[size:size*2]
            if first == second and len(first) >= 2:
                parts = first + parts[size*2:]
                break
    
    text = ' '.join(parts)
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = text.split(' ')
    unique_words = []
    for w in words:
        if not unique_words or w != unique_words[-1]:
            unique_words.append(w)
    text = ' '.join(unique_words)
    
    return text.strip()

def extract_name_and_position(text):
    text = clean_name_position(text)
    if not text:
        return '', ''
    
    words = text.split(' ')
    
    if len(words) <= 1:
        return text, ''
    
    name = ' '.join(words[:2])
    position = ' '.join(words[2:])
    
    return name, position

def parse_customer_data(raw_text):
    if not raw_text:
        return []
    
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    text = raw_text.strip()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    
    results = []
    
    email_matches = list(re.finditer(email_pattern, text))
    
    if not email_matches:
        return [{'name': text.strip(), 'position': '', 'email1': '', 'source': '', 'status': 'no_email'}]
    
    for i, match in enumerate(email_matches):
        email = match.group()
        
        start_pos = match.start()
        end_pos = match.end()
        
        if i > 0:
            prev_match = email_matches[i - 1]
            before_email = text[prev_match.end():start_pos]
        else:
            before_email = text[:start_pos]
        
        if i < len(email_matches) - 1:
            next_match = email_matches[i + 1]
            after_email = text[end_pos:next_match.start()]
        else:
            after_email = text[end_pos:]
        
        name, position = extract_name_and_position(before_email)
        
        after_email_clean = clean_source(after_email)
        
        words = after_email_clean.split(' ')
        if len(words) > 3:
            after_email_clean = ' '.join(words[:3])
        
        if '@' in after_email_clean:
            email_check_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_in_after = re.search(email_check_pattern, after_email_clean)
            if email_in_after:
                after_email_clean = after_email_clean[:email_in_after.start()].strip()
        
        source = after_email_clean
        
        results.append({
            'name': name,
            'position': position,
            'email1': email,
            'source': source,
            'status': 'ok'
        })
    
    return results

@bp.route('', methods=['GET'])
def index():
    return render_template('collect/input.html')

@bp.route('/preview', methods=['POST'])
def preview():
    raw_text = request.form.get('raw_data', '')
    parsed_data = parse_customer_data(raw_text)
    
    if not parsed_data:
        flash('未解析到有效数据', 'error')
        return redirect(url_for('collect.index'))
    
    session['parsed_data'] = parsed_data
    return render_template('collect/preview.html', data=parsed_data)

@bp.route('/confirm', methods=['POST'])
def confirm():
    from app import get_db_connection
    
    names = request.form.getlist('name')
    positions = request.form.getlist('position')
    emails = request.form.getlist('email')
    sources = request.form.getlist('source')
    
    if not names:
        flash('没有要保存的数据', 'error')
        return redirect(url_for('collect.index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    saved_count = 0
    for i in range(len(names)):
        name = names[i].strip() if i < len(names) else ''
        position = positions[i].strip() if i < len(positions) else ''
        email1 = emails[i].strip() if i < len(emails) else ''
        source = sources[i].strip() if i < len(sources) else ''
        
        if name and email1:
            cursor.execute(
                '''INSERT INTO customers (name, position, email1, source) 
                   VALUES (?, ?, ?, ?)''',
                (name, position, email1, source)
            )
            saved_count += 1
    
    conn.commit()
    conn.close()
    
    flash(f'成功保存 {saved_count} 条记录', 'success')
    return redirect(url_for('customers.list'))
