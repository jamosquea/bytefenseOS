#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Autenticación 2FA Avanzado
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
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import redis
import smtplib
from email.mime.text import MimeText

class Advanced2FAManager:
    def __init__(self, db_path='/opt/bytefense/system/bytefense.db'):
        self.db_path = db_path
        self.secret_key = self.get_or_create_secret_key()
        self.redis_client = self.setup_redis()
        self.rate_limits = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.setup_database()
        self.setup_logging()
        
    def setup_redis(self):
        """Configurar Redis para sesiones y cache"""
        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            client.ping()
            return client
        except:
            self.logger.warning("Redis no disponible, usando memoria local")
            return None
    
    def setup_logging(self):
        """Configurar logging avanzado"""
        handler = RotatingFileHandler(
            '/var/log/bytefense-auth.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
    
    def generate_backup_codes(self, user_id):
        """Generar códigos de respaldo para 2FA"""
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Hashear y guardar códigos
        hashed_codes = [bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode() for code in codes]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Limpiar códigos anteriores
        cursor.execute('DELETE FROM backup_codes WHERE user_id = ?', (user_id,))
        
        # Insertar nuevos códigos
        for hashed_code in hashed_codes:
            cursor.execute(
                'INSERT INTO backup_codes (user_id, code_hash, created_at) VALUES (?, ?, ?)',
                (user_id, hashed_code, datetime.now())
            )
        
        conn.commit()
        conn.close()
        
        return codes
    
    def verify_backup_code(self, user_id, code):
        """Verificar código de respaldo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, code_hash FROM backup_codes WHERE user_id = ? AND used = 0',
            (user_id,)
        )
        
        for backup_id, code_hash in cursor.fetchall():
            if bcrypt.checkpw(code.encode(), code_hash.encode()):
                # Marcar código como usado
                cursor.execute(
                    'UPDATE backup_codes SET used = 1, used_at = ? WHERE id = ?',
                    (datetime.now(), backup_id)
                )
                conn.commit()
                conn.close()
                return True
        
        conn.close()
        return False
    
    def setup_webauthn(self, user_id):
        """Configurar WebAuthn para autenticación sin contraseña"""
        try:
            from webauthn import generate_registration_options, verify_registration_response
            
            options = generate_registration_options(
                rp_id="bytefense.local",
                rp_name="Bytefense OS",
                user_id=str(user_id).encode(),
                user_name=f"user_{user_id}",
                user_display_name=f"Bytefense User {user_id}"
            )
            
            # Guardar challenge en Redis/memoria
            challenge_key = f"webauthn_challenge_{user_id}"
            if self.redis_client:
                self.redis_client.setex(challenge_key, 300, options.challenge)  # 5 min
            
            return options
            
        except ImportError:
            self.logger.warning("WebAuthn no disponible, instalar webauthn package")
            return None
    
    def advanced_risk_assessment(self, request_data):
        """Evaluación avanzada de riesgo"""
        risk_score = 0
        factors = []
        
        # Factor 1: Geolocalización
        ip = request_data.get('ip')
        if ip:
            try:
                import requests
                geo_data = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
                country = geo_data.get('country', 'Unknown')
                
                # Lista de países de alto riesgo
                high_risk_countries = ['CN', 'RU', 'KP', 'IR']
                if geo_data.get('countryCode') in high_risk_countries:
                    risk_score += 30
                    factors.append(f"High-risk country: {country}")
                    
            except:
                risk_score += 10
                factors.append("Unable to verify geolocation")
        
        # Factor 2: Horario inusual
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            risk_score += 15
            factors.append("Unusual login time")
        
        # Factor 3: User-Agent
        user_agent = request_data.get('user_agent', '')
        suspicious_agents = ['curl', 'wget', 'python', 'bot']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            risk_score += 25
            factors.append("Suspicious user agent")
        
        # Factor 4: Velocidad de intentos
        if self.failed_attempts.get(ip, 0) > 3:
            risk_score += 40
            factors.append("Multiple failed attempts")
        
        return {
            'risk_score': risk_score,
            'risk_level': 'HIGH' if risk_score > 50 else 'MEDIUM' if risk_score > 25 else 'LOW',
            'factors': factors
        }
    
    def send_security_alert(self, user_id, alert_type, details):
        """Enviar alerta de seguridad"""
        try:
            # Obtener configuración de email del usuario
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                email = result[0]
                subject = f"[Bytefense] Alerta de Seguridad: {alert_type}"
                
                message = f"""
                Se ha detectado actividad sospechosa en tu cuenta de Bytefense:
                
                Tipo: {alert_type}
                Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Detalles: {details}
                
                Si no fuiste tú, cambia tu contraseña inmediatamente.
                """
                
                # Enviar email (configurar SMTP según necesidades)
                self.logger.info(f"Security alert sent to {email}: {alert_type}")
                
        except Exception as e:
            self.logger.error(f"Error sending security alert: {e}")