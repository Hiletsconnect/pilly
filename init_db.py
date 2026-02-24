#!/usr/bin/env python3
"""
Database initialization script for ESP32 Management System
This script creates or resets the database with the default admin user
"""

import sqlite3
from werkzeug.security import generate_password_hash
import os

DATABASE = 'esp32_management.db'

def init_database():
    """Initialize or reset the database"""
    
    # Remove existing database if it exists
    if os.path.exists(DATABASE):
        print(f"Removing existing database: {DATABASE}")
        os.remove(DATABASE)
    
    print(f"Creating new database: {DATABASE}")
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # Users table
    print("Creating users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Devices table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Firmwares table
    print("Creating firmwares table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firmwares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            description TEXT,
            file_size INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Alarms table
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
    
    # Logs table
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
    
    # Create default admin user
    print("Creating default admin user...")
    hashed_password = generate_password_hash('admin123')
    cursor.execute(
        'INSERT INTO users (username, password) VALUES (?, ?)',
        ('admin', hashed_password)
    )
    
    db.commit()
    db.close()
    
    print("\n" + "="*50)
    print("Database initialized successfully!")
    print("="*50)
    print("\nDefault credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\n⚠️  Remember to change the default password after first login!")
    print("="*50 + "\n")

if __name__ == '__main__':
    init_database()
