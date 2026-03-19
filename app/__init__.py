import os
import sqlite3
from flask import Flask
from config import Config

def get_db_connection():
    db_path = Config.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position TEXT,
            email1 TEXT,
            email2 TEXT,
            phone1 TEXT,
            phone2 TEXT,
            company TEXT,
            nationality TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_email_sent_at TIMESTAMP DEFAULT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS smtp_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            smtp_host TEXT NOT NULL,
            smtp_port INTEGER DEFAULT 587,
            smtp_user TEXT NOT NULL,
            smtp_password TEXT NOT NULL,
            use_tls INTEGER DEFAULT 1,
            sender_name TEXT,
            sender_email TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS email_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            smtp_config_id INTEGER,
            subject TEXT,
            recipient_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES email_contents(id),
            FOREIGN KEY (smtp_config_id) REFERENCES smtp_settings(id)
        )
    ''')
    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    init_db()
    
    from app.routes import collect, customers, export, smtp, content, sender, logs
    app.register_blueprint(collect.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(smtp.bp)
    app.register_blueprint(content.bp)
    app.register_blueprint(sender.bp)
    app.register_blueprint(logs.bp)
    
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/collect')
    
    return app
