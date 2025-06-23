#!/usr/bin/env python3
"""
Bytefense OS - Sistema de Autenticación y Seguridad
Soporte para tokens, 2FA, rate limiting y protección CSRF
"""

import jwt
import bcrypt
import pyotp
import qrcode
import io
import base64
import sqlite3
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string
from collections import defaultdict
import logging

class AuthManager:
    def __init__(self, db_path='/opt/bytefense/intel/threats.db'):
        self.db_path = db_path
        self.secret_key = self.get_or_create_secret_key()
        self.rate_limits = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.setup_database()
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Configurar tablas de autenticación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                totp_secret TEXT,
                totp_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de tokens de API
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                user_id INTEGER,
                permissions TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                csrf_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de intentos de login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                username TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT
            )
        ''')
        
        # Crear usuario admin por defecto si no existe
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password('bytefense123')
            cursor.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                ('admin', admin_password, 'admin')
            )
            self.logger.info("Default admin user created (username: admin, password: bytefense123)")
        
        conn.commit()
        conn.close()
    
    def get_or_create_secret_key(self) -> str:
        """Obtener o crear clave secreta"""
        secret_file = '/opt/bytefense/system/.secret_key'
        try:
            with open(secret_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            secret = secrets.token_urlsafe(32)
            with open(secret_file, 'w') as f:
                f.write(secret)
            return secret
    
    def hash_password(self, password: str) -> str:
        """Hash de contraseña con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_totp_secret(self) -> str:
        """Generar secreto TOTP"""
        return pyotp.random_base32()
    
    def generate_totp_qr(self, username: str, secret: str) -> str:
        """Generar código QR para TOTP"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="Bytefense OS"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verificar token TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def create_jwt_token(self, user_id: int, username: str, role: str) -> str:
        """Crear token JWT"""
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> dict:
        """Verificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token expirado")
        except jwt.InvalidTokenError:
            raise Exception("Token inválido")
        except Exception as e:
            raise Exception(f"Error verificando token: {str(e)}")