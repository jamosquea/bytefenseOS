#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Sistema de Threat Intelligence Avanzado
"""

import requests
import json
import sqlite3
import time
import hashlib
import threading
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import feedparser
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import dns.resolver
import whois

class AdvancedThreatIntelligence:
    def __init__(self, db_path='/opt/bytefense/intel/threats.db'):
        self.db_path = db_path
        self.feeds = self.load_threat_feeds()
        self.api_keys = self.load_api_keys()
        self.setup_logging()
        self.setup_database()
        
    def load_threat_feeds(self):
        """Cargar feeds de threat intelligence"""
        return {
            'abuse_ch': {
                'malware_bazaar': 'https://bazaar.abuse.ch/export/json/recent/',
                'feodo_tracker': 'https://feodotracker.abuse.ch/downloads/ipblocklist.json',
                'ssl_blacklist': 'https://sslbl.abuse.ch/blacklist/sslipblacklist.json'
            },
            'alienvault': {
                'reputation': 'https://reputation.alienvault.com/reputation.data'
            },
            'emergingthreats': {
                'compromised_ips': 'https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt'
            },
            'spamhaus': {
                'drop': 'https://www.spamhaus.org/drop/drop.txt',
                'edrop': 'https://www.spamhaus.org/drop/edrop.txt'
            },
            'misp': {
                'events': 'https://misppriv.circl.lu/events/restSearch'
            }
        }
    
    def load_api_keys(self):
        """Cargar claves API desde archivo de configuración"""
        try:
            with open('/opt/bytefense/config/api_keys.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'virustotal': '',
                'shodan': '',
                'abuseipdb': '',
                'hybrid_analysis': ''
            }
    
    def setup_logging(self):
        """Configurar logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/bytefense-intel.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Configurar base de datos extendida"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de indicadores enriquecidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threat_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                type TEXT NOT NULL,
                confidence INTEGER DEFAULT 50,
                severity TEXT DEFAULT 'medium',
                source TEXT NOT NULL,
                tags TEXT,
                context TEXT,
                first_seen DATETIME NOT NULL,
                last_seen DATETIME NOT NULL,
                ttl INTEGER DEFAULT 86400,
                metadata TEXT,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de análisis de malware
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS malware_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_md5 TEXT,
                hash_sha1 TEXT,
                hash_sha256 TEXT,
                file_type TEXT,
                file_size INTEGER,
                family TEXT,
                analysis_date DATETIME,
                sandbox_report TEXT,
                yara_matches TEXT,
                behavior TEXT
            )
        ''')
        
        # Tabla de campañas de ataque
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attack_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                threat_actor TEXT,
                start_date DATETIME,
                end_date DATETIME,
                indicators TEXT,
                ttps TEXT,
                targets TEXT,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def enrich_ip_indicator(self, ip: str) -> Dict:
        """Enriquecer indicador IP con múltiples fuentes"""
        enrichment = {
            'ip': ip,
            'geolocation': {},
            'asn': {},
            'reputation': {},
            'malware_families': [],
            'open_ports': [],
            'certificates': [],
            'domains': []
        }
        
        # Geolocalización
        try:
            geo_response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
            if geo_response.status_code == 200:
                enrichment['geolocation'] = geo_response.json()
        except Exception as e:
            self.logger.warning(f"Error getting geolocation for {ip}: {e}")
        
        # Información ASN
        try:
            asn_response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=10)
            if asn_response.status_code == 200:
                data = asn_response.json()
                enrichment['asn'] = {
                    'asn': data.get('asn'),
                    'org': data.get('org'),
                    'isp': data.get('isp')
                }
        except Exception as e:
            self.logger.warning(f"Error getting ASN for {ip}: {e}")
        
        # VirusTotal (si hay API key)
        if self.api_keys.get('virustotal'):
            try:
                vt_headers = {'x-apikey': self.api_keys['virustotal']}
                vt_response = requests.get(
                    f'https://www.virustotal.com/api/v3/ip_addresses/{ip}',
                    headers=vt_headers,
                    timeout=10
                )
                if vt_response.status_code == 200:
                    vt_data = vt_response.json()
                    enrichment['reputation']['virustotal'] = {
                        'malicious': vt_data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('malicious', 0),
                        'suspicious': vt_data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {}).get('suspicious', 0)
                    }
            except Exception as e:
                self.logger.warning(f"Error querying VirusTotal for {ip}: {e}")
        
        # Shodan (si hay API key)
        if self.api_keys.get('shodan'):
            try:
                shodan_response = requests.get(
                    f'https://api.shodan.io/shodan/host/{ip}?key={self.api_keys["shodan"]}',
                    timeout=10
                )
                if shodan_response.status_code == 200:
                    shodan_data = shodan_response.json()
                    enrichment['open_ports'] = [service.get('port') for service in shodan_data.get('data', [])]
                    enrichment['domains'] = shodan_data.get('hostnames', [])
            except Exception as e:
                self.logger.warning(f"Error querying Shodan for {ip}: {e}")
        
        return enrichment
    
    def analyze_malware_sample(self, file_hash: str, hash_type: str = 'sha256') -> Dict:
        """Analizar muestra de malware"""
        analysis = {
            'hash': file_hash,
            'hash_type': hash_type,
            'detections': {},
            'behavior': {},
            'family': None,
            'confidence': 0
        }
        
        # VirusTotal análisis
        if self.api_keys.get('virustotal'):
            try:
                vt_headers = {'x-apikey': self.api_keys['virustotal']}
                vt_response = requests.get(
                    f'https://www.virustotal.com/api/v3/files/{file_hash}',
                    headers=vt_headers,
                    timeout=15
                )
                
                if vt_response.status_code == 200:
                    vt_data = vt_response.json()
                    attributes = vt_data.get('data', {}).get('attributes', {})
                    
                    analysis['detections']['virustotal'] = {
                        'malicious': attributes.get('last_analysis_stats', {}).get('malicious', 0),
                        'total_engines': sum(attributes.get('last_analysis_stats', {}).values()),
                        'names': list(set([result.get('result') for result in attributes.get('last_analysis_results', {}).values() if result.get('result')]))
                    }
                    
                    # Extraer familia de malware más común
                    names = analysis['detections']['virustotal']['names']
                    if names:
                        # Lógica simple para determinar familia
                        family_candidates = {}
                        for name in names:
                            parts = name.lower().split('.')
                            if len(parts) > 1:
                                family = parts[0]
                                family_candidates[family] = family_candidates.get(family, 0) + 1
                        
                        if family_candidates:
                            analysis['family'] = max(family_candidates, key=family_candidates.get)
                            analysis['confidence'] = (family_candidates[analysis['family']] / len(names)) * 100
                            
            except Exception as e:
                self.logger.warning(f"Error analyzing malware {file_hash}: {e}")
        
        return analysis
    
    def detect_attack_campaign(self, indicators: List[str]) -> Optional[Dict]:
        """Detectar campañas de ataque basadas en indicadores"""
        # Buscar patrones en indicadores
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar indicadores relacionados
        related_indicators = []
        for indicator in indicators:
            cursor.execute(
                'SELECT * FROM threat_indicators WHERE indicator LIKE ? OR tags LIKE ?',
                (f'%{indicator}%', f'%{indicator}%')
            )
            related_indicators.extend(cursor.fetchall())
        
        conn.close()
        
        if len(related_indicators) >= 3:  # Umbral mínimo para campaña
            campaign = {
                'name': f'Campaign_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'indicators': indicators,
                'confidence': min(100, len(related_indicators) * 10),
                'start_date': datetime.now() - timedelta(days=7),
                'description': f'Detected campaign with {len(related_indicators)} related indicators'
            }
            
            return campaign
        
        return None
    
    def update_all_feeds(self):
        """Actualizar todos los feeds de threat intelligence"""
        self.logger.info("Starting threat intelligence feeds update")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for source, feeds in self.feeds.items():
                for feed_name, url in feeds.items():
                    future = executor.submit(self.update_single_feed, source, feed_name, url)
                    futures.append(future)
            
            # Esperar a que terminen todos
            for future in futures:
                try:
                    future.result(timeout=60)
                except Exception as e:
                    self.logger.error(f"Error updating feed: {e}")
        
        self.logger.info("Threat intelligence feeds update completed")
    
    def update_single_feed(self, source: str, feed_name: str, url: str):
        """Actualizar un feed específico"""
        try:
            self.logger.info(f"Updating {source}/{feed_name}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Procesar según el tipo de feed
            if 'json' in url or feed_name.endswith('.json'):
                data = response.json()
                self.process_json_feed(source, feed_name, data)
            elif 'txt' in url or feed_name.endswith('.txt'):
                data = response.text
                self.process_text_feed(source, feed_name, data)
            else:
                self.logger.warning(f"Unknown feed format for {source}/{feed_name}")
                
        except Exception as e:
            self.logger.error(f"Error updating {source}/{feed_name}: {e}")
    
    def process_json_feed(self, source: str, feed_name: str, data: Dict):
        """Procesar feed en formato JSON"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indicators_added = 0
        
        # Procesar según la estructura del feed
        if source == 'abuse_ch' and feed_name == 'feodo_tracker':
            for item in data:
                if 'ip_address' in item:
                    cursor.execute('''
                        INSERT OR REPLACE INTO threat_indicators 
                        (indicator, type, source, confidence, first_seen, last_seen, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item['ip_address'],
                        'ip',
                        f'{source}/{feed_name}',
                        80,
                        datetime.now(),
                        datetime.now(),
                        json.dumps(item)
                    ))
                    indicators_added += 1
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Added {indicators_added} indicators from {source}/{feed_name}")
    
    def process_text_feed(self, source: str, feed_name: str, data: str):
        """Procesar feed en formato texto"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indicators_added = 0
        
        for line in data.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Detectar tipo de indicador
                indicator_type = self.detect_indicator_type(line)
                
                if indicator_type:
                    cursor.execute('''
                        INSERT OR REPLACE INTO threat_indicators 
                        (indicator, type, source, confidence, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        line,
                        indicator_type,
                        f'{source}/{feed_name}',
                        70,
                        datetime.now(),
                        datetime.now()
                    ))
                    indicators_added += 1
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Added {indicators_added} indicators from {source}/{feed_name}")
    
    def detect_indicator_type(self, indicator: str) -> Optional[str]:
        """Detectar tipo de indicador"""
        try:
            # Verificar si es IP
            ipaddress.ip_address(indicator)
            return 'ip'
        except:
            pass
        
        # Verificar si es dominio
        if '.' in indicator and not '/' in indicator:
            return 'domain'
        
        # Verificar si es hash
        if len(indicator) == 32:  # MD5
            return 'hash_md5'
        elif len(indicator) == 40:  # SHA1
            return 'hash_sha1'
        elif len(indicator) == 64:  # SHA256
            return 'hash_sha256'
        
        # Verificar si es URL
        if indicator.startswith(('http://', 'https://')):
            return 'url'
        
        return None