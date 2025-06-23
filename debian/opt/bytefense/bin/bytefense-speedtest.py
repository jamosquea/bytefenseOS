#!/usr/bin/env python3
# Bytefense OS - Módulo OpenSpeedTest
# Integración para monitoreo de velocidad de red

import os
import json
import time
import sqlite3
import requests
import subprocess
from datetime import datetime
from flask import Flask, render_template, jsonify

class BytefenseSpeedTest:
    def __init__(self):
        self.db_path = "/opt/bytefense/system/speedtest.db"
        self.config_path = "/opt/bytefense/system/speedtest-config.json"
        self.init_database()
        self.load_config()
    
    def init_database(self):
        """Inicializar base de datos para resultados de speedtest"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speedtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                download_speed REAL,
                upload_speed REAL,
                ping REAL,
                jitter REAL,
                server_info TEXT,
                test_type TEXT DEFAULT 'auto'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                interface_name TEXT,
                bytes_sent INTEGER,
                bytes_recv INTEGER,
                packets_sent INTEGER,
                packets_recv INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_config(self):
        """Cargar configuración del speedtest"""
        default_config = {
            "auto_test_interval": 3600,  # 1 hora
            "enabled": True,
            "max_results": 1000,
            "alert_thresholds": {
                "min_download": 10.0,  # Mbps
                "min_upload": 5.0,     # Mbps
                "max_ping": 100.0      # ms
            }
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def run_speedtest(self, test_type="auto"):
        """Ejecutar prueba de velocidad"""
        try:
            # Usar speedtest-cli si está disponible
            result = subprocess.run(
                ['speedtest-cli', '--json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Convertir a Mbps
                download_mbps = data['download'] / 1_000_000
                upload_mbps = data['upload'] / 1_000_000
                ping_ms = data['ping']
                
                # Guardar resultado
                self.save_result({
                    'download_speed': download_mbps,
                    'upload_speed': upload_mbps,
                    'ping': ping_ms,
                    'jitter': 0,  # speedtest-cli no proporciona jitter
                    'server_info': json.dumps(data.get('server', {})),
                    'test_type': test_type
                })
                
                # Verificar alertas
                self.check_alerts(download_mbps, upload_mbps, ping_ms)
                
                return {
                    'success': True,
                    'download': download_mbps,
                    'upload': upload_mbps,
                    'ping': ping_ms
                }
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def save_result(self, result):
        """Guardar resultado en base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO speedtest_results 
            (download_speed, upload_speed, ping, jitter, server_info, test_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result['download_speed'],
            result['upload_speed'],
            result['ping'],
            result['jitter'],
            result['server_info'],
            result['test_type']
        ))
        
        conn.commit()
        conn.close()
        
        # Limpiar resultados antiguos
        self.cleanup_old_results()
    
    def cleanup_old_results(self):
        """Limpiar resultados antiguos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM speedtest_results 
            WHERE id NOT IN (
                SELECT id FROM speedtest_results 
                ORDER BY timestamp DESC 
                LIMIT ?
            )
        ''', (self.config['max_results'],))
        
        conn.commit()
        conn.close()
    
    def check_alerts(self, download, upload, ping):
        """Verificar si se deben enviar alertas"""
        alerts = []
        thresholds = self.config['alert_thresholds']
        
        if download < thresholds['min_download']:
            alerts.append(f"Velocidad de descarga baja: {download:.2f} Mbps")
        
        if upload < thresholds['min_upload']:
            alerts.append(f"Velocidad de subida baja: {upload:.2f} Mbps")
        
        if ping > thresholds['max_ping']:
            alerts.append(f"Latencia alta: {ping:.2f} ms")
        
        if alerts:
            self.send_alerts(alerts)
    
    def send_alerts(self, alerts):
        """Enviar alertas al sistema de notificaciones"""
        try:
            # Integrar con el sistema de alertas de Bytefense
            alert_data = {
                'type': 'network_performance',
                'severity': 'warning',
                'message': '; '.join(alerts),
                'timestamp': datetime.now().isoformat()
            }
            
            # Enviar a la API de alertas
            requests.post(
                'http://localhost:8080/api/alerts',
                json=alert_data,
                timeout=5
            )
        except Exception as e:
            print(f"Error enviando alerta: {e}")
    
    def get_recent_results(self, limit=24):
        """Obtener resultados recientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, download_speed, upload_speed, ping, test_type
            FROM speedtest_results 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'timestamp': row[0],
            'download': row[1],
            'upload': row[2],
            'ping': row[3],
            'type': row[4]
        } for row in results]

if __name__ == "__main__":
    speedtest = BytefenseSpeedTest()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            result = speedtest.run_speedtest("manual")
            print(json.dumps(result, indent=2))
        elif sys.argv[1] == "daemon":
            # Modo daemon para pruebas automáticas
            while True:
                if speedtest.config['enabled']:
                    speedtest.run_speedtest("auto")
                time.sleep(speedtest.config['auto_test_interval'])