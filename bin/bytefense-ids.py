#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Detección de Intrusiones Avanzado
"""

import re
import time
import sqlite3
import threading
import subprocess
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
import psutil
import hashlib
import os

class AdvancedIDS:
    def __init__(self):
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.patterns = self.load_attack_patterns()
        self.connection_tracker = defaultdict(lambda: deque(maxlen=100))
        self.process_baseline = self.create_process_baseline()
        self.file_integrity = {}
        self.running = True
        
    def load_attack_patterns(self):
        """Cargar patrones de ataques conocidos"""
        return {
            'sql_injection': [
                r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
                r"(union|select|insert|delete|update|drop|create|alter)",
                r"(script|javascript|vbscript|onload|onerror)"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*="
            ],
            'directory_traversal': [
                r"\.\./",
                r"%2e%2e%2f",
                r"\\\.\.\\|"
            ],
            'command_injection': [
                r"(;|\||&|`|\$\(|\${)",
                r"(nc|netcat|wget|curl|python|perl|php|bash|sh)"
            ],
            'brute_force': [
                r"(admin|administrator|root|test|guest|user)",
                r"(password|passwd|123456|admin|root)"
            ]
        }
    
    def create_process_baseline(self):
        """Crear línea base de procesos normales"""
        baseline = set()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                baseline.add(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return baseline
    
    def monitor_network_connections(self):
        """Monitorear conexiones de red sospechosas"""
        while self.running:
            try:
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        
                        # Detectar conexiones a puertos sospechosos
                        suspicious_ports = [4444, 5555, 6666, 7777, 8888, 9999, 31337]
                        if remote_port in suspicious_ports:
                            self.log_suspicious_activity(
                                'suspicious_port_connection',
                                f"Connection to suspicious port {remote_port} on {remote_ip}"
                            )
                        
                        # Detectar múltiples conexiones desde la misma IP
                        self.connection_tracker[remote_ip].append(time.time())
                        recent_connections = sum(1 for t in self.connection_tracker[remote_ip] 
                                               if time.time() - t < 60)
                        
                        if recent_connections > 50:
                            self.log_suspicious_activity(
                                'connection_flood',
                                f"High connection rate from {remote_ip}: {recent_connections}/min"
                            )
                
                time.sleep(5)
                
            except Exception as e:
                print(f"Error monitoring connections: {e}")
                time.sleep(10)
    
    def monitor_process_anomalies(self):
        """Detectar procesos anómalos"""
        while self.running:
            try:
                current_processes = set()
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
                    try:
                        proc_info = proc.info
                        proc_name = proc_info['name']
                        current_processes.add(proc_name)
                        
                        # Detectar procesos nuevos no en baseline
                        if proc_name not in self.process_baseline:
                            cmdline = ' '.join(proc_info['cmdline'] or [])
                            
                            # Buscar patrones sospechosos en línea de comandos
                            for pattern_type, patterns in self.patterns.items():
                                for pattern in patterns:
                                    if re.search(pattern, cmdline, re.IGNORECASE):
                                        self.log_suspicious_activity(
                                            f'suspicious_process_{pattern_type}',
                                            f"Suspicious process: {proc_name} - {cmdline}"
                                        )
                        
                        # Detectar uso excesivo de CPU
                        if proc_info['cpu_percent'] and proc_info['cpu_percent'] > 90:
                            self.log_suspicious_activity(
                                'high_cpu_usage',
                                f"High CPU usage by {proc_name}: {proc_info['cpu_percent']}%"
                            )
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                time.sleep(30)
                
            except Exception as e:
                print(f"Error monitoring processes: {e}")
                time.sleep(60)
    
    def monitor_file_integrity(self, paths_to_monitor):
        """Monitorear integridad de archivos críticos"""
        for path in paths_to_monitor:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                    self.file_integrity[path] = file_hash
        
        while self.running:
            try:
                for path in paths_to_monitor:
                    if os.path.exists(path):
                        with open(path, 'rb') as f:
                            current_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        if path in self.file_integrity:
                            if self.file_integrity[path] != current_hash:
                                self.log_suspicious_activity(
                                    'file_integrity_violation',
                                    f"File modified: {path}"
                                )
                                self.file_integrity[path] = current_hash
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error monitoring file integrity: {e}")
                time.sleep(600)
    
    def log_suspicious_activity(self, activity_type, description):
        """Registrar actividad sospechosa"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO events (event_type, description, severity, date) VALUES (?, ?, ?, ?)",
                (activity_type, description, 3, datetime.now())
            )
            
            conn.commit()
            conn.close()
            
            print(f"[IDS ALERT] {activity_type}: {description}")
            
        except Exception as e:
            print(f"Error logging suspicious activity: {e}")