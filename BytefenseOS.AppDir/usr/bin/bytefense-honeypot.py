#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Honeypots Inteligentes
"""

import socket
import threading
import time
import sqlite3
import json
import random
import string
from datetime import datetime
import subprocess

class IntelligentHoneypot:
    def __init__(self):
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.honeypots = {
            'ssh': {'port': 2222, 'service': 'SSH'},
            'ftp': {'port': 2121, 'service': 'FTP'},
            'telnet': {'port': 2323, 'service': 'Telnet'},
            'http': {'port': 8081, 'service': 'HTTP'},
            'smtp': {'port': 2525, 'service': 'SMTP'}
        }
        self.fake_responses = self.load_fake_responses()
        self.running = True
    
    def load_fake_responses(self):
        """Cargar respuestas falsas convincentes"""
        return {
            'ssh': {
                'banner': 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5',
                'login_prompt': 'login: ',
                'password_prompt': 'Password: ',
                'failed_login': 'Login incorrect',
                'fake_shell': '$ '
            },
            'ftp': {
                'banner': '220 ProFTPD 1.3.6 Server ready.',
                'user_prompt': '331 Password required for {}.',
                'login_failed': '530 Login incorrect.',
                'commands': {
                    'USER': '331 Password required for {}.',
                    'PASS': '230 User {} logged in.',
                    'SYST': '215 UNIX Type: L8',
                    'PWD': '257 "/" is current directory.',
                    'LIST': '150 Opening ASCII mode data connection.'
                }
            },
            'http': {
                'headers': 'HTTP/1.1 200 OK\r\nServer: Apache/2.4.41\r\nContent-Type: text/html\r\n\r\n',
                'fake_pages': {
                    '/': '<html><head><title>Welcome</title></head><body><h1>Server Status</h1><p>System operational</p></body></html>',
                    '/admin': '<html><head><title>Admin Login</title></head><body><form><input type="text" placeholder="Username"><input type="password" placeholder="Password"><button>Login</button></form></body></html>',
                    '/login.php': '<html><head><title>Login</title></head><body><form method="post"><input name="user"><input name="pass" type="password"><input type="submit"></form></body></html>'
                }
            }
        }
    
    def start_ssh_honeypot(self):
        """Honeypot SSH interactivo"""
        def handle_ssh_client(client_socket, addr):
            try:
                # Enviar banner SSH
                client_socket.send(f"{self.fake_responses['ssh']['banner']}\r\n".encode())
                
                # Simular proceso de login
                client_socket.send(self.fake_responses['ssh']['login_prompt'].encode())
                username = client_socket.recv(1024).decode().strip()
                
                client_socket.send(self.fake_responses['ssh']['password_prompt'].encode())
                password = client_socket.recv(1024).decode().strip()
                
                # Registrar intento de login
                self.log_honeypot_activity('ssh_login_attempt', addr[0], {
                    'username': username,
                    'password': password,
                    'service': 'SSH',
                    'port': 2222
                })
                
                # Simular shell falsa por un tiempo
                client_socket.send(f"{self.fake_responses['ssh']['failed_login']}\r\n".encode())
                
                # Mantener conexión para recopilar más información
                for _ in range(3):
                    client_socket.send(self.fake_responses['ssh']['login_prompt'].encode())
                    try:
                        data = client_socket.recv(1024).decode().strip()
                        if data:
                            self.log_honeypot_activity('ssh_additional_attempt', addr[0], {
                                'data': data,
                                'service': 'SSH'
                            })
                    except:
                        break
                
            except Exception as e:
                print(f"SSH honeypot error: {e}")
            finally:
                client_socket.close()
        
        # Servidor SSH honeypot
        ssh_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssh_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ssh_server.bind(('0.0.0.0', 2222))
        ssh_server.listen(5)
        
        print("SSH Honeypot listening on port 2222")
        
        while self.running:
            try:
                client_socket, addr = ssh_server.accept()
                thread = threading.Thread(target=handle_ssh_client, args=(client_socket, addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"SSH honeypot accept error: {e}")
    
    def start_http_honeypot(self):
        """Honeypot HTTP con páginas falsas"""
        def handle_http_client(client_socket, addr):
            try:
                request = client_socket.recv(4096).decode()
                
                # Parsear request HTTP
                lines = request.split('\r\n')
                if lines:
                    request_line = lines[0]
                    method, path, version = request_line.split(' ', 2)
                    
                    # Registrar acceso
                    self.log_honeypot_activity('http_access', addr[0], {
                        'method': method,
                        'path': path,
                        'user_agent': self.extract_header(lines, 'User-Agent'),
                        'service': 'HTTP',
                        'port': 8081
                    })
                    
                    # Responder con página falsa
                    if path in self.fake_responses['http']['fake_pages']:
                        response_body = self.fake_responses['http']['fake_pages'][path]
                    else:
                        response_body = self.fake_responses['http']['fake_pages']['/']
                    
                    response = self.fake_responses['http']['headers'] + response_body
                    client_socket.send(response.encode())
                    
                    # Si es POST, capturar datos
                    if method == 'POST':
                        post_data = request.split('\r\n\r\n', 1)
                        if len(post_data) > 1:
                            self.log_honeypot_activity('http_post_data', addr[0], {
                                'path': path,
                                'data': post_data[1],
                                'service': 'HTTP'
                            })
                
            except Exception as e:
                print(f"HTTP honeypot error: {e}")
            finally:
                client_socket.close()
        
        # Servidor HTTP honeypot
        http_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        http_server.bind(('0.0.0.0', 8081))
        http_server.listen(5)
        
        print("HTTP Honeypot listening on port 8081")
        
        while self.running:
            try:
                client_socket, addr = http_server.accept()
                thread = threading.Thread(target=handle_http_client, args=(client_socket, addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"HTTP honeypot accept error: {e}")
    
    def extract_header(self, lines, header_name):
        """Extraer header específico de request HTTP"""
        for line in lines:
            if line.startswith(f"{header_name}:"):
                return line.split(':', 1)[1].strip()
        return 'Unknown'
    
    def log_honeypot_activity(self, activity_type, source_ip, details):
        """Registrar actividad del honeypot"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            description = f"{activity_type} from {source_ip}: {json.dumps(details)}"
            
            cursor.execute(
                "INSERT INTO events (event_type, source_ip, description, severity, date) VALUES (?, ?, ?, ?, ?)",
                (activity_type, source_ip, description, 2, datetime.now())
            )
            
            # También agregar IP a lista de amenazas si es un intento de login
            if 'login_attempt' in activity_type:
                cursor.execute(
                    "INSERT OR IGNORE INTO blocked_ips (ip, reason, date) VALUES (?, ?, ?)",
                    (source_ip, f"Honeypot {activity_type}", datetime.now())
                )
            
            conn.commit()
            conn.close()
            
            print(f"[HONEYPOT] {activity_type} from {source_ip}")
            
            # Auto-bloquear IP después de múltiples intentos
            self.auto_block_aggressive_ips(source_ip)
            
        except Exception as e:
            print(f"Error logging honeypot activity: {e}")
    
    def auto_block_aggressive_ips(self, ip):
        """Bloquear automáticamente IPs agresivas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar eventos de esta IP en la última hora
            cursor.execute(
                "SELECT COUNT(*) FROM events WHERE source_ip = ? AND date > datetime('now', '-1 hour')",
                (ip,)
            )
            
            count = cursor.fetchone()[0]
            
            if count >= 5:  # 5 o más intentos en una hora
                # Bloquear con UFW
                try:
                    subprocess.run(['ufw', 'deny', 'from', ip], check=True, capture_output=True)
                    print(f"[AUTO-BLOCK] IP {ip} blocked after {count} honeypot interactions")
                except subprocess.CalledProcessError:
                    print(f"[ERROR] Failed to block IP {ip}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error in auto-block: {e}")