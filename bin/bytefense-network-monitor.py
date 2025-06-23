#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Monitor Avanzado de Red con IA
Sistema completo de monitoreo de nodos, aplicaciones, sitios web y análisis de riesgos
"""

import psutil
import socket
import subprocess
import json
import time
import requests
import sqlite3
import threading
import re
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

class AdvancedNetworkMonitor:
    def __init__(self):
        self.db_path = 'c:/proyectos/bytefense/data/network_monitor.db'
        self.ai_models_path = 'c:/proyectos/bytefense/models/'
        self.setup_database()
        self.setup_ai_models()
        
        self.network_data = {
            'nodes': {},
            'bandwidth': defaultdict(lambda: {'download': 0, 'upload': 0, 'apps': {}}),
            'visited_sites': deque(maxlen=1000),
            'risk_analysis': {},
            'ai_insights': {},
            'topology': {}
        }
        
        self.risk_categories = {
            'malware': ['malware', 'virus', 'trojan', 'ransomware'],
            'phishing': ['phishing', 'scam', 'fake', 'suspicious'],
            'ads': ['ads', 'advertisement', 'tracker', 'analytics'],
            'social': ['facebook', 'twitter', 'instagram', 'tiktok'],
            'streaming': ['youtube', 'netflix', 'spotify', 'twitch'],
            'gaming': ['steam', 'epic', 'origin', 'battle.net'],
            'work': ['office', 'teams', 'zoom', 'slack'],
            'development': ['github', 'gitlab', 'stackoverflow', 'docker']
        }
        
        self.running = True
        
    def setup_database(self):
        """Configurar base de datos SQLite"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de actividad de red por nodo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                node_ip TEXT,
                node_name TEXT,
                app_name TEXT,
                bandwidth_down REAL,
                bandwidth_up REAL,
                connections_count INTEGER,
                risk_level TEXT,
                category TEXT
            )
        ''')
        
        # Tabla de sitios visitados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visited_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                node_ip TEXT,
                url TEXT,
                domain TEXT,
                category TEXT,
                risk_level TEXT,
                blocked BOOLEAN DEFAULT FALSE,
                response_time REAL
            )
        ''')
        
        # Tabla de topología de red
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_topology (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_ip TEXT,
                dest_ip TEXT,
                protocol TEXT,
                port INTEGER,
                status TEXT
            )
        ''')
        
        # Tabla de análisis de IA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                analysis_type TEXT,
                node_ip TEXT,
                anomaly_score REAL,
                threat_level TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_ai_models(self):
        """Configurar modelos de IA"""
        os.makedirs(self.ai_models_path, exist_ok=True)
        
        # Modelo de detección de anomalías
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Modelo de clustering para patrones de ataque
        self.attack_clusterer = DBSCAN(
            eps=0.5,
            min_samples=5
        )
        
        # Escalador para normalización
        self.scaler = StandardScaler()
        
        # Cargar modelos pre-entrenados si existen
        try:
            self.anomaly_detector = joblib.load(f'{self.ai_models_path}anomaly_model.pkl')
            self.scaler = joblib.load(f'{self.ai_models_path}scaler.pkl')
        except:
            print("Modelos de IA no encontrados, usando modelos nuevos")
    
    def discover_network_nodes(self):
        """Descubrir y analizar nodos en la red"""
        nodes = []
        
        try:
            # Obtener información del nodo local
            local_ip = self.get_local_ip()
            local_node = {
                'ip': local_ip,
                'name': socket.gethostname(),
                'type': 'local',
                'os': self.detect_os(local_ip),
                'apps': self.get_running_apps(local_ip),
                'bandwidth': self.get_bandwidth_usage(local_ip),
                'risk_level': 'low',
                'last_seen': datetime.now().isoformat(),
                'connections': self.get_active_connections(local_ip)
            }
            nodes.append(local_node)
            
            # Escanear red local para otros dispositivos
            network_range = self.get_network_range()
            discovered_ips = self.scan_network(network_range)
            
            for ip in discovered_ips:
                if ip != local_ip:
                    node = {
                        'ip': ip,
                        'name': self.get_hostname(ip),
                        'type': self.identify_device_type(ip),
                        'os': self.detect_os(ip),
                        'apps': self.get_running_apps(ip),
                        'bandwidth': self.get_bandwidth_usage(ip),
                        'risk_level': self.calculate_risk_level(ip),
                        'last_seen': datetime.now().isoformat(),
                        'connections': self.get_active_connections(ip)
                    }
                    nodes.append(node)
            
            # Guardar en base de datos
            self.save_network_activity(nodes)
            
            return nodes
            
        except Exception as e:
            print(f"Error discovering nodes: {e}")
            return []
    
    def get_running_apps(self, ip):
        """Obtener aplicaciones ejecutándose en un nodo"""
        apps = []
        
        try:
            if ip == self.get_local_ip():
                # Para el nodo local, usar psutil
                for proc in psutil.process_iter(['pid', 'name', 'connections', 'memory_info', 'cpu_percent']):
                    try:
                        if proc.info['connections']:
                            app_info = {
                                'name': proc.info['name'],
                                'pid': proc.info['pid'],
                                'memory': proc.info['memory_info'].rss if proc.info['memory_info'] else 0,
                                'cpu': proc.info['cpu_percent'] or 0,
                                'connections': len(proc.info['connections']),
                                'risk': self.classify_app_risk(proc.info['name'])
                            }
                            apps.append(app_info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
                # Limitar a las 20 aplicaciones más activas
                apps = sorted(apps, key=lambda x: x['connections'], reverse=True)[:20]
            else:
                # Para nodos remotos, usar técnicas de fingerprinting
                apps = self.fingerprint_remote_apps(ip)
                
        except Exception as e:
            print(f"Error getting apps for {ip}: {e}")
            
        return apps
    
    def analyze_visited_sites(self):
        """Analizar sitios web visitados con categorización avanzada"""
        visited_sites = []
        
        try:
            # Analizar logs de DNS (Pi-hole si está disponible)
            pihole_logs = [
                '/var/log/pihole.log',
                'c:/proyectos/bytefense/logs/dns.log'
            ]
            
            for log_path in pihole_logs:
                if os.path.exists(log_path):
                    visited_sites.extend(self.parse_dns_log(log_path))
            
            # Analizar logs de navegador si están disponibles
            browser_logs = self.get_browser_history()
            visited_sites.extend(browser_logs)
            
            # Procesar y categorizar sitios
            processed_sites = []
            for site in visited_sites[-200:]:  # Últimos 200 sitios
                processed_site = {
                    'timestamp': site.get('timestamp', datetime.now().isoformat()),
                    'client_ip': site.get('client_ip', 'unknown'),
                    'url': site.get('url', ''),
                    'domain': self.extract_domain(site.get('url', '')),
                    'category': self.categorize_domain(site.get('url', '')),
                    'risk_level': self.classify_domain_risk(site.get('url', '')),
                    'blocked': site.get('blocked', False),
                    'response_time': site.get('response_time', 0)
                }
                processed_sites.append(processed_site)
            
            # Guardar en base de datos
            self.save_visited_sites(processed_sites)
            
            return processed_sites
            
        except Exception as e:
            print(f"Error analyzing visited sites: {e}")
            return []
    
    def generate_ai_insights(self):
        """Generar insights usando IA"""
        insights = {
            'anomalies': [],
            'patterns': [],
            'predictions': [],
            'recommendations': []
        }
        
        try:
            # Obtener datos para análisis
            network_data = self.get_network_metrics()
            
            if len(network_data) > 10:  # Necesitamos suficientes datos
                # Detectar anomalías
                anomalies = self.detect_anomalies(network_data)
                insights['anomalies'] = anomalies
                
                # Identificar patrones
                patterns = self.identify_patterns(network_data)
                insights['patterns'] = patterns
                
                # Generar predicciones
                predictions = self.generate_predictions(network_data)
                insights['predictions'] = predictions
                
                # Crear recomendaciones
                recommendations = self.generate_recommendations(anomalies, patterns)
                insights['recommendations'] = recommendations
            
            return insights
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return insights
    
    def get_network_topology(self):
        """Generar mapa de topología de red"""
        topology = {
            'nodes': [],
            'connections': [],
            'subnets': [],
            'gateways': []
        }
        
        try:
            # Obtener nodos activos
            nodes = self.discover_network_nodes()
            topology['nodes'] = nodes
            
            # Mapear conexiones entre nodos
            connections = self.map_connections()
            topology['connections'] = connections
            
            # Identificar subredes
            subnets = self.identify_subnets()
            topology['subnets'] = subnets
            
            # Encontrar gateways
            gateways = self.find_gateways()
            topology['gateways'] = gateways
            
            return topology
            
        except Exception as e:
            print(f"Error getting network topology: {e}")
            return topology
    
    # Métodos auxiliares
    def get_local_ip(self):
        """Obtener IP local"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def classify_domain_risk(self, domain):
        """Clasificar riesgo de un dominio"""
        if not domain:
            return 'unknown'
            
        domain = domain.lower()
        
        # Patrones de alto riesgo
        high_risk_patterns = [
            r'.*\.tk$', r'.*\.ml$', r'.*\.ga$', r'.*\.cf$',
            r'.*phishing.*', r'.*malware.*', r'.*suspicious.*',
            r'.*\.bit$', r'.*\.onion$'
        ]
        
        # Patrones de riesgo medio
        medium_risk_patterns = [
            r'.*ads.*', r'.*tracker.*', r'.*analytics.*',
            r'.*doubleclick.*', r'.*googleadservices.*'
        ]
        
        for pattern in high_risk_patterns:
            if re.match(pattern, domain):
                return 'high'
        
        for pattern in medium_risk_patterns:
            if re.match(pattern, domain):
                return 'medium'
        
        return 'low'
    
    def categorize_domain(self, url):
        """Categorizar dominio por tipo de contenido"""
        if not url:
            return 'unknown'
            
        url = url.lower()
        
        for category, keywords in self.risk_categories.items():
            if any(keyword in url for keyword in keywords):
                return category
        
        return 'other'
    
    def get_full_dashboard_data(self):
        """Obtener todos los datos para el dashboard"""
        return {
            'nodes': self.discover_network_nodes(),
            'visited_sites': self.analyze_visited_sites(),
            'ai_insights': self.generate_ai_insights(),
            'topology': self.get_network_topology(),
            'statistics': self.get_network_statistics(),
            'alerts': self.get_active_alerts(),
            'timestamp': datetime.now().isoformat()
        }

# API Flask
app = Flask(__name__)
CORS(app)
monitor = AdvancedNetworkMonitor()

@app.route('/api/network/nodes')
def get_nodes():
    return jsonify(monitor.discover_network_nodes())

@app.route('/api/network/sites')
def get_visited_sites():
    return jsonify(monitor.analyze_visited_sites())

@app.route('/api/network/ai-insights')
def get_ai_insights():
    return jsonify(monitor.generate_ai_insights())

@app.route('/api/network/topology')
def get_topology():
    return jsonify(monitor.get_network_topology())

@app.route('/api/network/dashboard')
def get_dashboard_data():
    return jsonify(monitor.get_full_dashboard_data())

@app.route('/api/network/statistics')
def get_statistics():
    return jsonify(monitor.get_network_statistics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)