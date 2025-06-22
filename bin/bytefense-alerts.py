#!/usr/bin/env python3
"""
Bytefense OS - Sistema de Alertas y Notificaciones
Soporte para Telegram, SMTP y notificaciones web
"""

import json
import sqlite3
import smtplib
import requests
import time
import logging
import subprocess
import os
import signal  # ← FALTANTE - AGREGAR ESTA LÍNEA
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional
import threading
import queue

class AlertManager:
    def __init__(self, config_file='/opt/bytefense/system/alerts.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.alert_queue = queue.Queue()
        self.running = True
        
        # Crear directorio de logs si no existe
        os.makedirs('/var/log', exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/bytefense-alerts.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Iniciar worker thread
        self.worker_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.worker_thread.start()
        
    def load_config(self) -> Dict:
        """Cargar configuración de alertas"""
        default_config = {
            "enabled": True,
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "smtp": {
                "enabled": False,
                "server": "smtp.gmail.com",
                "port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": []
            },
            "webhooks": {
                "enabled": False,
                "urls": []
            },
            "alert_types": {
                "blocked_ips": {
                    "enabled": True,
                    "threshold": 10,
                    "interval": 300
                },
                "service_down": {
                    "enabled": True,
                    "services": ["bytefense-dashboard", "bytefense-watch"]
                },
                "node_disconnected": {
                    "enabled": True,
                    "timeout": 600
                },
                "high_traffic": {
                    "enabled": True,
                    "threshold": 1000000
                },
                "honeypot_activity": {
                    "enabled": True,
                    "threshold": 5
                }
            }
        }
        
        try:
            # AGREGAR validación de directorio
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge con configuración por defecto
                return {**default_config, **config}
        except FileNotFoundError:
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            self.logger.error(f"Error al leer configuración: {self.config_file}")
            return default_config
    
    def save_config(self, config: Dict):
        """Guardar configuración"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {e}")
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'medium', data: Dict = None):
        """Enviar alerta al queue para procesamiento"""
        if not self.config.get('enabled', True):
            return
            
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        self.alert_queue.put(alert)
        self.logger.info(f"Alerta encolada: {alert_type} - {message}")
    
    def _process_alerts(self):
        """Procesar alertas del queue"""
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._send_alert_to_channels(alert)
                self._store_alert(alert)
                self.alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error procesando alerta: {e}")
    
    def _send_alert_to_channels(self, alert: Dict):
        """Enviar alerta a todos los canales configurados"""
        message = self._format_alert_message(alert)
        
        # Telegram
        if self.config['telegram']['enabled']:
            self._send_telegram(message, alert)
        
        # SMTP
        if self.config['smtp']['enabled']:
            self._send_email(message, alert)
        
        # Webhooks
        if self.config['webhooks']['enabled']:
            self._send_webhooks(alert)
    
    def _format_alert_message(self, alert: Dict) -> str:
        """Formatear mensaje de alerta"""
        severity_emoji = {
            'low': '🟡',
            'medium': '🟠', 
            'high': '🔴',
            'critical': '💀'
        }
        
        emoji = severity_emoji.get(alert['severity'], '⚪')
        timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"{emoji} **BYTEFENSE ALERT**\n\n"
        message += f"**Tipo:** {alert['type']}\n"
        message += f"**Severidad:** {alert['severity'].upper()}\n"
        message += f"**Tiempo:** {timestamp}\n"
        message += f"**Mensaje:** {alert['message']}\n"
        
        if alert['data']:
            message += f"\n**Detalles:**\n"
            for key, value in alert['data'].items():
                message += f"• {key}: {value}\n"
        
        return message
    
    def _send_telegram(self, message: str, alert: Dict):
        try:
            bot_token = self.config['telegram']['bot_token']
            chat_id = self.config['telegram']['chat_id']
            
            if not bot_token or not chat_id:
                self.logger.warning("Configuración de Telegram incompleta")  # ← AGREGAR warning
                return
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.logger.info("Alerta enviada por Telegram")
            else:
                self.logger.error(f"Error enviando Telegram: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error en Telegram: {e}")
    
    def _send_email(self, message: str, alert: Dict):
        """Enviar alerta por email"""
        try:
            smtp_config = self.config['smtp']
            
            if not smtp_config['username'] or not smtp_config['to_emails']:
                return
            
            msg = MimeMultipart()
            msg['From'] = smtp_config['from_email'] or smtp_config['username']
            msg['Subject'] = f"Bytefense Alert: {alert['type']} ({alert['severity']})"
            
            plain_message = message.replace('**', '').replace('*', '')
            msg.attach(MimeText(plain_message, 'plain'))
            
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            
            for to_email in smtp_config['to_emails']:
                msg['To'] = to_email
                server.send_message(msg)
                del msg['To']
            
            server.quit()
            self.logger.info("Alerta enviada por email")
            
        except Exception as e:
            self.logger.error(f"Error en email: {e}")
            # AGREGAR manejo seguro del servidor
            try:
                if 'server' in locals():
                    server.quit()
            except:
                pass
    
    def _send_webhooks(self, alert: Dict):
        try:
            for url in self.config['webhooks']['urls']:
                try:  # ← AGREGAR try individual
                    response = requests.post(
                        url, 
                        json=alert, 
                        timeout=10,
                        headers={'Content-Type': 'application/json'}
                    )
                    if response.status_code == 200:
                        self.logger.info(f"Webhook enviado a {url}")
                    else:
                        self.logger.error(f"Error webhook {url}: {response.status_code}")
                except requests.RequestException as e:  # ← AGREGAR manejo específico
                    self.logger.error(f"Error conectando webhook {url}: {e}")
        except Exception as e:
            self.logger.error(f"Error en webhooks: {e}")
    
    def _store_alert(self, alert: Dict):
        try:
            import os
            if not os.path.exists(self.db_path):  # ← AGREGAR validación
                self.logger.error(f"Base de datos no encontrada: {self.db_path}")
                return
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (event_type, source_ip, details, timestamp, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"alert_{alert['type']}",
                alert['data'].get('source_ip', 'system'),
                json.dumps(alert),
                alert['timestamp'],
                alert['severity']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error almacenando alerta: {e}")

class AlertMonitor:
    """Monitor que verifica condiciones y genera alertas"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.last_checks = {}
        
    def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        while True:
            try:
                self.check_blocked_ips()
                self.check_services()
                self.check_nodes()
                self.check_honeypot_activity()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logging.error(f"Error en monitoreo: {e}")
                time.sleep(60)
    
    def check_blocked_ips(self):
        """Verificar IPs bloqueadas recientes"""
        config = self.alert_manager.config['alert_types']['blocked_ips']
        if not config['enabled']:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar IPs bloqueadas en el último intervalo
            since = datetime.now() - timedelta(seconds=config['interval'])
            cursor.execute("""
                SELECT COUNT(*) FROM blocked_ips 
                WHERE created_at > ?
            """, (since.isoformat(),))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count >= config['threshold']:
                self.alert_manager.send_alert(
                    'blocked_ips',
                    f"Se han bloqueado {count} IPs en los últimos {config['interval']} segundos",
                    'medium',
                    {'count': count, 'interval': config['interval']}
                )
                
        except Exception as e:
            logging.error(f"Error verificando IPs bloqueadas: {e}")
    
    def check_services(self):
        """Verificar estado de servicios críticos"""
        config = self.alert_manager.config['alert_types']['service_down']
        
        if not config['enabled']:
            return
        
        try:
            for service in config['services']:
                try:
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        # Verificar si ya se envió alerta recientemente
                        last_alert_key = f"service_down_{service}"
                        last_alert = self.alert_manager.config.get('last_alerts', {}).get(last_alert_key, 0)
                        
                        if time.time() - last_alert > 300:  # 5 minutos
                            self.alert_manager.send_alert(
                                'service_down',
                                f"El servicio {service} está inactivo",
                                'high',
                                {'service': service, 'status': result.stdout.strip()}
                            )
                            
                            # Actualizar timestamp de última alerta
                            if 'last_alerts' not in self.alert_manager.config:
                                self.alert_manager.config['last_alerts'] = {}
                            self.alert_manager.config['last_alerts'][last_alert_key] = time.time()
                            self.alert_manager.save_config(self.alert_manager.config)
                            
                    except subprocess.TimeoutExpired:
                        logging.error(f"Timeout verificando servicio {service}")
                    except Exception as e:
                        logging.error(f"Error verificando servicio {service}: {e}")
                except Exception as e:
                    logging.error(f"Error general verificando servicios: {e}")
    
    def check_nodes(self):
        """Verificar nodos conectados"""
        config = self.alert_manager.config['alert_types']['node_disconnected']
        if not config['enabled']:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar nodos que no han enviado heartbeat recientemente
            timeout = datetime.now() - timedelta(seconds=config['timeout'])
            cursor.execute("""
                SELECT node_id, node_name, last_seen 
                FROM registered_nodes 
                WHERE last_seen < ? AND status = 'online'
            """, (timeout.isoformat(),))
            
            disconnected_nodes = cursor.fetchall()
            conn.close()
            
            for node_id, node_name, last_seen in disconnected_nodes:
                # Marcar como offline
                self._update_node_status(node_id, 'offline')
                
                self.alert_manager.send_alert(
                    'node_disconnected',
                    f"El nodo {node_name} ({node_id}) se ha desconectado",
                    'medium',
                    {
                        'node_id': node_id,
                        'node_name': node_name,
                        'last_seen': last_seen
                    }
                )
                
        except Exception as e:
            logging.error(f"Error verificando nodos: {e}")
    
    def check_honeypot_activity(self):
        """Verificar actividad del honeypot"""
        config = self.alert_manager.config['alert_types']['honeypot_activity']
        if not config['enabled']:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar eventos de honeypot en la última hora
            since = datetime.now() - timedelta(hours=1)
            cursor.execute("""
                SELECT COUNT(*) FROM events 
                WHERE event_type LIKE 'honeypot_%' AND timestamp > ?
            """, (since.isoformat(),))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            if count >= config['threshold']:
                self.alert_manager.send_alert(
                    'honeypot_activity',
                    f"Detectada actividad sospechosa: {count} intentos en honeypot",
                    'high',
                    {'attempts': count, 'period': '1 hour'}
                )
                
        except Exception as e:
            logging.error(f"Error verificando honeypot: {e}")
    
    def _update_node_status(self, node_id: str, status: str):
        """Actualizar estado de nodo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE registered_nodes SET status = ? WHERE node_id = ?",
                (status, node_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error actualizando estado de nodo: {e}")

def main():
    """Función principal"""
    print("🚨 Iniciando sistema de alertas Bytefense...")
    
    # Crear manager de alertas PRIMERO
    alert_manager = AlertManager()
    
    def signal_handler(signum, frame):
        print("\n🛑 Deteniendo sistema de alertas...")
        alert_manager.running = False
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Crear monitor
    monitor = AlertMonitor(alert_manager)
    
    # Iniciar monitoreo
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema de alertas...")
        alert_manager.running = False

if __name__ == '__main__':
    main()