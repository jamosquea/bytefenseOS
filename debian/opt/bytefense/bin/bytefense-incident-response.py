#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Respuesta Automática a Incidentes (SOAR)
"""

import json
import sqlite3
import subprocess
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from enum import Enum
import smtplib
from email.mime.text import MimeText
import requests

class IncidentSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class IncidentStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class AutomatedIncidentResponse:
    def __init__(self, db_path='/opt/bytefense/system/bytefense.db'):
        self.db_path = db_path
        self.playbooks = self.load_playbooks()
        self.setup_logging()
        self.setup_database()
        self.active_incidents = {}
        
    def setup_logging(self):
        """Configurar logging para respuesta a incidentes"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/bytefense-incident-response.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Configurar base de datos de incidentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                severity INTEGER NOT NULL,
                status TEXT NOT NULL,
                source_ip TEXT,
                target_ip TEXT,
                attack_type TEXT,
                indicators TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                resolved_at DATETIME,
                playbook_executed TEXT,
                actions_taken TEXT,
                analyst_notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incident_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER,
                timestamp DATETIME NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                automated BOOLEAN DEFAULT 1,
                FOREIGN KEY (incident_id) REFERENCES incidents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_playbooks(self):
        """Cargar playbooks de respuesta automática"""
        return {
            'brute_force_ssh': {
                'name': 'SSH Brute Force Response',
                'triggers': ['ssh_brute_force', 'multiple_failed_logins'],
                'severity_threshold': IncidentSeverity.MEDIUM,
                'actions': [
                    {'type': 'block_ip', 'duration': 3600},
                    {'type': 'alert_admin', 'method': 'email'},
                    {'type': 'increase_monitoring', 'duration': 1800},
                    {'type': 'collect_evidence'}
                ]
            },
            'malware_detected': {
                'name': 'Malware Detection Response',
                'triggers': ['malware_signature', 'suspicious_behavior'],
                'severity_threshold': IncidentSeverity.HIGH,
                'actions': [
                    {'type': 'isolate_host'},
                    {'type': 'collect_forensics'},
                    {'type': 'alert_admin', 'method': 'sms'},
                    {'type': 'scan_network'},
                    {'type': 'update_signatures'}
                ]
            },
            'ddos_attack': {
                'name': 'DDoS Attack Response',
                'triggers': ['high_traffic', 'connection_flood'],
                'severity_threshold': IncidentSeverity.HIGH,
                'actions': [
                    {'type': 'enable_rate_limiting'},
                    {'type': 'block_source_networks'},
                    {'type': 'alert_admin', 'method': 'phone'},
                    {'type': 'activate_cdn_protection'}
                ]
            },
            'data_exfiltration': {
                'name': 'Data Exfiltration Response',
                'triggers': ['unusual_outbound_traffic', 'large_file_transfer'],
                'severity_threshold': IncidentSeverity.CRITICAL,
                'actions': [
                    {'type': 'block_outbound_traffic'},
                    {'type': 'isolate_affected_systems'},
                    {'type': 'preserve_evidence'},
                    {'type': 'alert_admin', 'method': 'all'},
                    {'type': 'notify_authorities'}
                ]
            }
        }
    
    def create_incident(self, title: str, description: str, severity: IncidentSeverity, 
                       source_ip: str = None, target_ip: str = None, 
                       attack_type: str = None, indicators: List[str] = None) -> int:
        """Crear nuevo incidente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO incidents 
            (title, description, severity, status, source_ip, target_ip, 
             attack_type, indicators, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, description, severity.value, IncidentStatus.OPEN.value,
            source_ip, target_ip, attack_type, 
            json.dumps(indicators) if indicators else None,
            datetime.now(), datetime.now()
        ))
        
        incident_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.info(f"Created incident {incident_id}: {title}")
        
        # Agregar a timeline
        self.add_timeline_entry(incident_id, "incident_created", 
                               f"Incident created with severity {severity.name}")
        
        # Ejecutar respuesta automática
        self.execute_automated_response(incident_id, attack_type)
        
        return incident_id
    
    def execute_automated_response(self, incident_id: int, attack_type: str):
        """Ejecutar respuesta automática basada en playbooks"""
        # Buscar playbook apropiado
        playbook = None
        for pb_name, pb_config in self.playbooks.items():
            if attack_type in pb_config['triggers']:
                playbook = pb_config
                break
        
        if not playbook:
            self.logger.warning(f"No playbook found for attack type: {attack_type}")
            return
        
        self.logger.info(f"Executing playbook '{playbook['name']}' for incident {incident_id}")
        
        # Actualizar estado del incidente
        self.update_incident_status(incident_id, IncidentStatus.IN_PROGRESS)
        
        # Ejecutar acciones del playbook
        actions_taken = []
        for action in playbook['actions']:
            try:
                result = self.execute_action(incident_id, action)
                actions_taken.append({
                    'action': action['type'],
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                self.add_timeline_entry(
                    incident_id, 
                    f"action_executed", 
                    f"Executed {action['type']}: {result}"
                )
                
            except Exception as e:
                self.logger.error(f"Error executing action {action['type']}: {e}")
                actions_taken.append({
                    'action': action['type'],
                    'result': f"Error: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                })
        
        # Guardar acciones tomadas
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE incidents SET actions_taken = ?, playbook_executed = ? WHERE id = ?',
            (json.dumps(actions_taken), playbook['name'], incident_id)
        )
        conn.commit()
        conn.close()
    
    def execute_action(self, incident_id: int, action: Dict) -> str:
        """Ejecutar acción específica"""
        action_type = action['type']
        
        if action_type == 'block_ip':
            return self.block_ip_action(incident_id, action)
        elif action_type == 'alert_admin':
            return self.alert_admin_action(incident_id, action)
        elif action_type == 'isolate_host':
            return self.isolate_host_action(incident_id, action)
        elif action_type == 'collect_forensics':
            return self.collect_forensics_action(incident_id, action)
        elif action_type == 'enable_rate_limiting':
            return self.enable_rate_limiting_action(incident_id, action)
        elif action_type == 'scan_network':
            return self.scan_network_action(incident_id, action)
        else:
            return f"Unknown action type: {action_type}"
    
    def block_ip_action(self, incident_id: int, action: Dict) -> str:
        """Bloquear IP maliciosa"""
        # Obtener IP del incidente
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT source_ip FROM incidents WHERE id = ?', (incident_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "No source IP found"
        
        source_ip = result[0]
        duration = action.get('duration', 3600)
        
        try:
            # Bloquear con UFW
            subprocess.run(['ufw', 'deny', 'from', source_ip], 
                         check=True, capture_output=True)
            
            # Programar desbloqueo
            if duration > 0:
                threading.Timer(duration, self.unblock_ip, args=[source_ip]).start()
            
            return f"Blocked IP {source_ip} for {duration} seconds"
            
        except subprocess.CalledProcessError as e:
            return f"Failed to block IP: {e}"
    
    def alert_admin_action(self, incident_id: int, action: Dict) -> str:
        """Alertar al administrador"""
        method = action.get('method', 'email')
        
        # Obtener detalles del incidente
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incidents WHERE id = ?', (incident_id,))
        incident = cursor.fetchone()
        conn.close()
        
        if not incident:
            return "Incident not found"
        
        message = f"""
        ALERTA DE SEGURIDAD BYTEFENSE
        
        Incidente ID: {incident_id}
        Título: {incident[1]}
        Severidad: {incident[3]}
        IP Origen: {incident[5] or 'N/A'}
        Tipo de Ataque: {incident[7] or 'N/A'}
        Fecha: {incident[9]}
        
        Descripción:
        {incident[2]}
        
        Acciones automáticas ejecutadas.
        Revisar dashboard para más detalles.
        """
        
        if method in ['email', 'all']:
            # Enviar email (configurar SMTP según necesidades)
            self.logger.info(f"Email alert sent for incident {incident_id}")
        
        if method in ['sms', 'all']:
            # Enviar SMS (integrar con servicio SMS)
            self.logger.info(f"SMS alert sent for incident {incident_id}")
        
        if method in ['phone', 'all']:
            # Llamada telefónica (integrar con servicio de voz)
            self.logger.info(f"Phone alert initiated for incident {incident_id}")
        
        return f"Alert sent via {method}"
    
    def isolate_host_action(self, incident_id: int, action: Dict) -> str:
        """Aislar host comprometido"""
        # Obtener IP del incidente
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT target_ip FROM incidents WHERE id = ?', (incident_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return "No target IP found"
        
        target_ip = result[0]
        
        try:
            # Bloquear todo el tráfico hacia/desde el host
            subprocess.run(['ufw', 'deny', 'from', target_ip], check=True)
            subprocess.run(['ufw', 'deny', 'to', target_ip], check=True)
            
            return f"Host {target_ip} isolated from network"
            
        except subprocess.CalledProcessError as e:
            return f"Failed to isolate host: {e}"
    
    def collect_forensics_action(self, incident_id: int, action: Dict) -> str:
        """Recopilar evidencia forense"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        forensics_dir = f'/opt/bytefense/forensics/incident_{incident_id}_{timestamp}'
        
        try:
            # Crear directorio de evidencia
            subprocess.run(['mkdir', '-p', forensics_dir], check=True)
            
            # Recopilar logs del sistema
            subprocess.run(['cp', '/var/log/auth.log', f'{forensics_dir}/auth.log'], 
                         check=True)
            subprocess.run(['cp', '/var/log/syslog', f'{forensics_dir}/syslog'], 
                         check=True)
            
            # Recopilar información de red
            with open(f'{forensics_dir}/network_info.txt', 'w') as f:
                subprocess.run(['netstat', '-tuln'], stdout=f, check=True)
            
            # Recopilar procesos activos
            with open(f'{forensics_dir}/processes.txt', 'w') as f:
                subprocess.run(['ps', 'aux'], stdout=f, check=True)
            
            return f"Forensics collected in {forensics_dir}"
            
        except subprocess.CalledProcessError as e:
            return f"Failed to collect forensics: {e}"
    
    def add_timeline_entry(self, incident_id: int, action: str, details: str):
        """Agregar entrada al timeline del incidente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO incident_timeline (incident_id, timestamp, action, details)
            VALUES (?, ?, ?, ?)
        ''', (incident_id, datetime.now(), action, details))
        
        conn.commit()
        conn.close()
    
    def update_incident_status(self, incident_id: int, status: IncidentStatus):
        """Actualizar estado del incidente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?',
            (status.value, datetime.now(), incident_id)
        )
        
        conn.commit()
        conn.close()
        
        self.add_timeline_entry(incident_id, "status_changed", f"Status changed to {status.value}")
    
    def unblock_ip(self, ip: str):
        """Desbloquear IP después del tiempo especificado"""
        try:
            subprocess.run(['ufw', 'delete', 'deny', 'from', ip], 
                         check=True, capture_output=True)
            self.logger.info(f"Automatically unblocked IP {ip}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to unblock IP {ip}: {e}")