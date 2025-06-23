#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Alertas Seguro con Validación y Rate Limiting
"""

import json
import sqlite3
import smtplib
import requests
import time
import logging
import subprocess
import os
import signal  # ← CORREGIDO: Import agregado
import threading
import queue
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional
from logging.handlers import RotatingFileHandler
import ssl
import re

class SecureAlertManager:
    def __init__(self, config_file='/opt/bytefense/system/alerts.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.alert_queue = queue.Queue(maxsize=1000)  # Límite de cola
        self.running = True
        self.rate_limits = {}
        
        # Configurar logging con rotación
        self.setup_logging()
        
        # Validar configuración
        self.validate_config()
        
        # Iniciar worker thread
        self.worker_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.worker_thread.start()
        
        # Configurar manejo de señales
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def setup_logging(self):
        """Configurar logging con rotación automática"""
        os.makedirs('/var/log', exist_ok=True)
        
        # Handler con rotación (max 10MB, 5 archivos)
        handler = RotatingFileHandler(
            '/var/log/bytefense-alerts.log',
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
        
        # También log a consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def validate_config(self):
        """Validar configuración de alertas"""
        try:
            # Validar configuración SMTP
            if self.config.get('smtp', {}).get('enabled', False):
                smtp_config = self.config['smtp']
                required_fields = ['server', 'port', 'username', 'password', 'from_email']
                
                for field in required_fields:
                    if not smtp_config.get(field):
                        self.logger.warning(f"SMTP: Campo requerido '{field}' faltante")
                        self.config['smtp']['enabled'] = False
                
                # Validar emails
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, smtp_config.get('from_email', '')):
                    self.logger.warning("SMTP: Email 'from_email' inválido")
                    self.config['smtp']['enabled'] = False
            
            # Validar configuración Telegram
            if self.config.get('telegram', {}).get('enabled', False):
                telegram_config = self.config['telegram']
                if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
                    self.logger.warning("Telegram: Token o chat_id faltante")
                    self.config['telegram']['enabled'] = False
            
            self.logger.info("Configuración validada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error validando configuración: {e}")
    
    def _signal_handler(self, signum, frame):
        """Manejo seguro de señales"""
        self.logger.info(f"Señal {signum} recibida, cerrando AlertManager...")
        self.running = False
        
    def send_secure_email(self, subject: str, message: str, to_emails: List[str]):
        """Enviar email con configuración segura"""
        try:
            smtp_config = self.config['smtp']
            
            # Crear mensaje
            msg = MimeMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[Bytefense] {subject}"
            
            msg.attach(MimeText(message, 'plain', 'utf-8'))
            
            # Conexión segura SMTP
            context = ssl.create_default_context()
            
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            self.logger.info(f"Email enviado: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando email: {e}")
            return False
    
    def check_rate_limit(self, alert_type: str, limit_minutes: int = 5) -> bool:
        """Verificar rate limiting para alertas"""
        now = time.time()
        
        if alert_type not in self.rate_limits:
            self.rate_limits[alert_type] = []
        
        # Limpiar alertas antiguas
        cutoff = now - (limit_minutes * 60)
        self.rate_limits[alert_type] = [
            timestamp for timestamp in self.rate_limits[alert_type] 
            if timestamp > cutoff
        ]
        
        # Verificar límite (máximo 3 alertas del mismo tipo en 5 minutos)
        if len(self.rate_limits[alert_type]) >= 3:
            return False
        
        self.rate_limits[alert_type].append(now)
        return True

# ... resto del código con mejoras de seguridad ...