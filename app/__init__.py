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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    init_db()
    
    from app.routes import collect, customers, export
    app.register_blueprint(collect.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(export.bp)
    
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/collect')
    
    return app
