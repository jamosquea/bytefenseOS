#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema 2FA Completo con TOTP y Backup Codes
"""

import pyotp
import qrcode
import io
import base64
import secrets
import sqlite3
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session

class TwoFactorAuth:
    def __init__(self, db_path='/opt/bytefense/system/bytefense.db'):
        self.db_path = db_path
        self.setup_2fa_tables()
    
    def setup_2fa_tables(self):
        """Configurar tablas para 2FA"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla para códigos de backup
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                code_hash TEXT NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla para dispositivos confiables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trusted_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                device_fingerprint TEXT NOT NULL,
                device_name TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_totp_secret(self, username):
        """Generar secreto TOTP para usuario"""
        secret = pyotp.random_base32()
        
        # Crear URI para QR
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="Bytefense OS"
        )
        
        # Generar QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f"data:image/png;base64,{img_str}",
            'manual_entry_key': secret
        }
    
    def generate_backup_codes(self, user_id, count=10):
        """Generar códigos de backup"""
        codes = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for _ in range(count):
            # Generar código de 8 dígitos
            code = f"{secrets.randbelow(100000000):08d}"
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            cursor.execute(
                "INSERT INTO backup_codes (user_id, code_hash) VALUES (?, ?)",
                (user_id, code_hash)
            )
            codes.append(code)
        
        conn.commit()
        conn.close()
        
        return codes
    
    def verify_totp(self, secret, token):
        """Verificar token TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def verify_backup_code(self, user_id, code):
        """Verificar código de backup"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM backup_codes WHERE user_id = ? AND code_hash = ? AND used = 0",
            (user_id, code_hash)
        )
        
        result = cursor.fetchone()
        if result:
            # Marcar como usado
            cursor.execute(
                "UPDATE backup_codes SET used = 1, used_at = CURRENT_TIMESTAMP WHERE id = ?",
                (result[0],)
            )
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False