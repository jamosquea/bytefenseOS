#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - API REST Segura con Autenticación y Validación
"""

import json
import sqlite3
import datetime
import os
import re
import hashlib
import secrets
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import logging
from functools import wraps
from collections import defaultdict
import jwt
import bcrypt

# Configuración segura
DB_PATH = "/opt/bytefense/system/bytefense.db"
API_PORT = 8080
SECRET_KEY = os.environ.get('BYTEFENSE_SECRET', secrets.token_hex(32))
RATE_LIMIT_WINDOW = 60  # segundos
RATE_LIMIT_REQUESTS = 100

# Rate limiting
rate_limits = defaultdict(list)

class SecurityMiddleware:
    @staticmethod
    def validate_ip(ip):
        """Validar formato de IP"""
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, ip))
    
    @staticmethod
    def validate_domain(domain):
        """Validar formato de dominio"""
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'r'[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def sanitize_path(path):
        """Sanitizar rutas para prevenir path traversal"""
        # Remover caracteres peligrosos
        path = re.sub(r'[^a-zA-Z0-9._/-]', '', path)
        # Prevenir path traversal
        path = os.path.normpath(path)
        if '..' in path or path.startswith('/'):
            raise ValueError("Path traversal detectado")
        return path
    
    @staticmethod
    def rate_limit_check(client_ip):
        """Verificar rate limiting"""
        now = time.time()
        # Limpiar requests antiguos
        rate_limits[client_ip] = [req_time for req_time in rate_limits[client_ip] 
                                 if now - req_time < RATE_LIMIT_WINDOW]
        
        if len(rate_limits[client_ip]) >= RATE_LIMIT_REQUESTS:
            return False
        
        rate_limits[client_ip].append(now)
        return True

class SecureDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()
    
    def execute_query(self, query, params=None):
        """Ejecutar consulta con parámetros seguros"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return [dict(row) for row in result]
                else:
                    conn.commit()
                    return cursor.rowcount
                    
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")
                raise
            finally:
                if conn:
                    conn.close()

class SecureByteFenseAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = SecureDatabase(DB_PATH)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        client_ip = self.client_address[0]
        
        # Rate limiting
        if not SecurityMiddleware.rate_limit_check(client_ip):
            self.send_error(429, "Rate limit exceeded")
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            # Sanitizar path
            safe_path = SecurityMiddleware.sanitize_path(path)
            
            # Routing seguro
            if path == "/" or path == "/index.html":
                self.serve_static_file("/opt/bytefense/web/index.html", "text/html")
            elif path.startswith("/static/"):
                # Validar que solo se sirvan archivos permitidos
                allowed_extensions = ['.css', '.js', '.png', '.jpg', '.ico']
                if any(path.endswith(ext) for ext in allowed_extensions):
                    self.serve_static_file(f"/opt/bytefense/web{safe_path}", 
                                         self.get_content_type(path))
                else:
                    self.send_error(403, "File type not allowed")
            elif path == "/api/status":
                self.handle_get_status()
            elif path == "/api/threats":
                self.handle_get_threats()
            elif path == "/api/events":
                self.handle_get_events()
            else:
                self.send_error(404, "Endpoint not found")
                
        except ValueError as e:
            self.send_error(400, str(e))
        except Exception as e:
            logging.error(f"Request error: {e}")
            self.send_error(500, "Internal server error")
    
    def handle_get_threats(self):
        """Obtener amenazas con consultas parametrizadas"""
        try:
            # Consulta segura con parámetros
            query = """
                SELECT 
                    strftime('%H', date) as hour,
                    COUNT(*) as count
                FROM blocked_ips 
                WHERE date >= datetime('now', '-24 hours')
                GROUP BY strftime('%H', date)
                ORDER BY hour
            """
            
            hourly_data = self.db.execute_query(query)
            
            # Procesar datos de forma segura
            hours = []
            counts = []
            
            for i in range(24):
                hour = (datetime.datetime.now().hour - 23 + i) % 24
                hour_str = f"{hour:02d}"
                hours.append(f"{hour_str}:00")
                
                # Buscar datos para esta hora
                count = 0
                for row in hourly_data:
                    if row['hour'] == f"{hour:02d}":
                        count = row['count']
                        break
                counts.append(count)
            
            response_data = {
                "hours": hours,
                "counts": counts,
                "total_blocked": sum(counts)
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            logging.error(f"Error getting threats: {e}")
            self.send_error(500, "Error retrieving threat data")
    
    def send_json_response(self, data):
        """Enviar respuesta JSON segura"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

# ... resto del código con mejoras de seguridad ...