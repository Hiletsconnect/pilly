#!/usr/bin/env python3
"""
Database initialization script for Pilly Cloud (Pastilleros Inteligentes)
Creates or resets the SQLite database with the default admin user.
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'esp32_management.db'

def init_database():
    # Remove existing database if it exists
    if os.path.exists(DATABASE):
        print(f"Removing existing database: {DATABASE}")
        os.remove(DATABASE)

    print(f"Creating new database: {DATABASE}")
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    print("Creating users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print("Creating devices table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac_address TEXT UNIQUE NOT NULL,
            device_name TEXT,
            ip_address TEXT,
            ssid TEXT,
            firmware_version TEXT,
            last_seen TIMESTAMP,
            status TEXT DEFAULT 'offline',
            uptime INTEGER DEFAULT 0,
            free_heap INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_key TEXT,
            admin_state TEXT DEFAULT 'active',
            ota_enabled INTEGER DEFAULT 0,
            ota_target_version TEXT
        )
    ''')

    print("Creating firmwares table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firmwares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            description TEXT,
            file_size INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_stable INTEGER DEFAULT 0
        )
    ''')

    print("Creating alarms table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            alarm_type TEXT NOT NULL,
            message TEXT,
            severity TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')

    print("Creating logs table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            log_type TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')

    print("Creating device_commands table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            command TEXT NOT NULL,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            ack_at TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')

    print("Creating default admin user (admin/admin123)...")
    cursor.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        ('admin', generate_password_hash('admin123'))
    )

    db.commit()
    db.close()
    print("✅ Database ready!")

if __name__ == '__main__':
    init_database()
