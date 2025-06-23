#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - API REST para gestión de nodos y datos de dashboard
"""

import json
import sqlite3
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import os
import random

DB_PATH = "/opt/bytefense/system/bytefense.db"
API_PORT = 8080

class BytefenseAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Servir archivos estáticos
        if path == "/" or path == "/index.html":
            self.serve_static_file("/opt/bytefense/web/index.html", "text/html")
        elif path.startswith("/static/"):
            self.serve_static_file(f"/opt/bytefense/web{path}", "text/css" if path.endswith('.css') else "application/javascript")
        # APIs
        elif path == "/api/nodes":
            self.handle_get_nodes()
        elif path == "/api/status":
            self.handle_get_status()
        elif path == "/api/threats":
            self.handle_get_threats()
        elif path == "/api/events":
            self.handle_get_events()
        elif path == "/api/vpn":
            self.handle_get_vpn_status()
        elif path == "/api/intel":
            self.handle_get_intel()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/register":
            self.handle_register_node()
        elif path == "/api/heartbeat":
            self.handle_heartbeat()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_static_file(self, file_path, content_type):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, f"Error serving file: {str(e)}")
    
    def handle_get_threats(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Obtener amenazas por hora en las últimas 24 horas
            cursor.execute("""
                SELECT 
                    strftime('%H', date) as hour,
                    COUNT(*) as count
                FROM blocked_ips 
                WHERE date >= datetime('now', '-24 hours')
                GROUP BY strftime('%H', date)
                ORDER BY hour
            """)
            
            hourly_data = cursor.fetchall()
            
            # Llenar horas faltantes con 0
            hours = []
            counts = []
            
            for i in range(24):
                hour = (datetime.datetime.now().hour - 23 + i) % 24
                hour_str = f"{hour:02d}"
                hours.append(f"{hour_str}:00")
                
                # Buscar datos para esta hora
                found = False
                for h, c in hourly_data:
                    if h == hour_str:
                        counts.append(c)
                        found = True
                        break
                if not found:
                    counts.append(0)
            
            # Obtener top amenazas
            cursor.execute("""
                SELECT ip, reason, COUNT(*) as count
                FROM blocked_ips 
                WHERE date >= datetime('now', '-24 hours')
                GROUP BY ip, reason
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_threats = [{
                "ip": row[0],
                "reason": row[1],
                "count": row[2]
            } for row in cursor.fetchall()]
            
            conn.close()
            
            response = {
                "status": "success",
                "hourly": {
                    "hours": hours,
                    "counts": counts
                },
                "top_threats": top_threats
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_get_events(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Eventos por tipo
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM events 
                WHERE date >= datetime('now', '-24 hours')
                GROUP BY event_type
                ORDER BY count DESC
            """)
            
            events_by_type = [{
                "type": row[0],
                "count": row[1]
            } for row in cursor.fetchall()]
            
            # Eventos recientes
            cursor.execute("""
                SELECT event_type, source_ip, description, 
                       datetime(date, 'localtime') as local_date
                FROM events 
                ORDER BY date DESC 
                LIMIT 20
            """)
            
            recent_events = [{
                "type": row[0],
                "source_ip": row[1],
                "description": row[2],
                "date": row[3]
            } for row in cursor.fetchall()]
            
            conn.close()
            
            response = {
                "status": "success",
                "by_type": events_by_type,
                "recent": recent_events
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_get_vpn_status(self):
        try:
            # Simular datos de VPN (en producción se obtendría de WireGuard)
            clients = [
                {"name": "Cliente-01", "ip": "10.8.0.2", "status": "connected", "last_seen": "2024-01-15 14:30:00"},
                {"name": "Cliente-02", "ip": "10.8.0.3", "status": "connected", "last_seen": "2024-01-15 14:25:00"},
                {"name": "Cliente-03", "ip": "10.8.0.4", "status": "disconnected", "last_seen": "2024-01-15 12:15:00"},
                {"name": "Cliente-04", "ip": "10.8.0.5", "status": "connected", "last_seen": "2024-01-15 14:32:00"},
                {"name": "Cliente-05", "ip": "10.8.0.6", "status": "disconnected", "last_seen": "2024-01-15 10:45:00"}
            ]
            
            connected = len([c for c in clients if c["status"] == "connected"])
            total = len(clients)
            
            # Datos de tráfico simulados
            traffic_data = {
                "hours": [f"{(datetime.datetime.now().hour - 11 + i) % 24:02d}:00" for i in range(12)],
                "upload": [random.randint(10, 100) for _ in range(12)],
                "download": [random.randint(50, 300) for _ in range(12)]
            }
            
            response = {
                "status": "success",
                "clients": clients,
                "summary": {
                    "total": total,
                    "connected": connected,
                    "disconnected": total - connected
                },
                "traffic": traffic_data
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_get_intel(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Obtener indicadores de amenazas
            cursor.execute("""
                SELECT indicator, type, source, confidence, tags,
                       datetime(last_seen, 'localtime') as last_seen
                FROM threat_intel 
                ORDER BY last_seen DESC 
                LIMIT 50
            """)
            
            indicators = [{
                "indicator": row[0],
                "type": row[1],
                "source": row[2],
                "confidence": row[3],
                "tags": row[4],
                "last_seen": row[5]
            } for row in cursor.fetchall()]
            
            # Estadísticas por tipo
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM threat_intel 
                GROUP BY type
                ORDER BY count DESC
            """)
            
            by_type = [{
                "type": row[0],
                "count": row[1]
            } for row in cursor.fetchall()]
            
            conn.close()
            
            response = {
                "status": "success",
                "indicators": indicators,
                "by_type": by_type
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_register_node(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, "No data provided")
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validar campos requeridos
            required_fields = ['node_id', 'node_name', 'node_type', 'ip_address']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    self.send_error(400, f"Campo requerido faltante o vacío: {field}")
                    return
            
            # Validar tipo de nodo
            if data['node_type'] not in ['master', 'satellite']:
                self.send_error(400, "node_type debe ser 'master' o 'satellite'")
                return
                
            # Validar formato de IP
            import ipaddress
            try:
                ipaddress.ip_address(data['ip_address'])
            except ValueError:
                self.send_error(400, "Formato de IP inválido")
                return
            
            # Conectar a la base de datos
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Insertar o actualizar nodo
            cursor.execute("""
                INSERT OR REPLACE INTO registered_nodes 
                (node_id, node_name, node_type, ip_address, public_ip, port, version, 
                 status, last_heartbeat, first_registered, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'online', datetime('now'), 
                        COALESCE((SELECT first_registered FROM registered_nodes WHERE node_id = ?), datetime('now')), ?)
            """, (
                data['node_id'],
                data['node_name'],
                data['node_type'],
                data['ip_address'],
                data.get('public_ip'),
                data.get('port', 8080),
                data.get('version', '1.0.0'),
                data['node_id'],
                json.dumps(data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            
            # Registrar evento
            self.log_event("NODE_REGISTER", data['ip_address'], f"Node {data['node_name']} registered")
            
            # Respuesta exitosa
            response = {
                "status": "success",
                "message": "Node registered successfully",
                "node_id": data['node_id']
            }
            
            self.send_json_response(response)
            
        except json.JSONDecodeError as e:
            self.send_error(400, f"JSON inválido: {str(e)}")
        except Exception as e:
            self.send_error(500, f"Error interno: {str(e)}")
            self.log_event('ERROR', self.client_address[0], f"Error en registro de nodo: {str(e)}")
    
    def handle_heartbeat(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if 'node_id' not in data:
                self.send_error(400, "Missing node_id")
                return
            
            # Conectar a la base de datos
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Actualizar heartbeat
            cursor.execute("""
                UPDATE registered_nodes 
                SET last_heartbeat = datetime('now'), 
                    status = ?, 
                    metadata = ?
                WHERE node_id = ?
            """, (
                data.get('status', 'online'),
                json.dumps(data.get('metrics', {})),
                data['node_id']
            ))
            
            if cursor.rowcount == 0:
                self.send_error(404, "Node not found")
                return
            
            conn.commit()
            conn.close()
            
            # Respuesta exitosa
            response = {"status": "success", "message": "Heartbeat received"}
            self.send_json_response(response)
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_get_nodes(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT node_id, node_name, node_type, ip_address, public_ip, 
                       port, version, status, last_heartbeat, first_registered, metadata
                FROM registered_nodes 
                ORDER BY last_heartbeat DESC
            """)
            
            nodes = []
            for row in cursor.fetchall():
                node = {
                    "node_id": row[0],
                    "node_name": row[1],
                    "node_type": row[2],
                    "ip_address": row[3],
                    "public_ip": row[4],
                    "port": row[5],
                    "version": row[6],
                    "status": row[7],
                    "last_heartbeat": row[8],
                    "first_registered": row[9],
                    "metadata": json.loads(row[10]) if row[10] else {}
                }
                nodes.append(node)
            
            conn.close()
            
            response = {
                "status": "success",
                "nodes": nodes,
                "total": len(nodes)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_get_status(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Obtener estadísticas generales
            cursor.execute("SELECT COUNT(*) FROM registered_nodes")
            total_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM registered_nodes WHERE status = 'online'")
            online_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM blocked_ips WHERE date >= date('now', '-24 hours')")
            blocked_ips_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM events WHERE date >= date('now', '-24 hours')")
            events_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM threat_intel")
            total_intel = cursor.fetchone()[0]
            
            conn.close()
            
            response = {
                "status": "success",
                "statistics": {
                    "total_nodes": total_nodes,
                    "online_nodes": online_nodes,
                    "offline_nodes": total_nodes - online_nodes,
                    "blocked_ips_24h": blocked_ips_24h,
                    "events_24h": events_24h,
                    "total_intel": total_intel,
                    "uptime": self.get_uptime()
                }
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def log_event(self, event_type, source_ip, description):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (event_type, source_ip, description, date)
                VALUES (?, ?, ?, datetime('now'))
            """, (event_type, source_ip, description))
            
            conn.commit()
            conn.close()
        except:
            pass  # No fallar si no se puede registrar el evento
    
    def get_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            return f"{uptime_seconds:.0f} seconds"
        except:
            return "unknown"
    
    def log_message(self, format, *args):
        # Suprimir logs de acceso para reducir ruido
        pass

def cleanup_offline_nodes():
    """Marcar nodos como offline si no han enviado heartbeat en 5 minutos"""
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE registered_nodes 
                SET status = 'offline' 
                WHERE datetime(last_heartbeat) < datetime('now', '-5 minutes')
                AND status != 'offline'
            """)
            
            if cursor.rowcount > 0:
                print(f"Marked {cursor.rowcount} nodes as offline")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in cleanup: {e}")
        
        time.sleep(60)  # Verificar cada minuto

if __name__ == "__main__":
    # Iniciar hilo de limpieza
    cleanup_thread = threading.Thread(target=cleanup_offline_nodes, daemon=True)
    cleanup_thread.start()
    
    # Iniciar servidor HTTP
    server = HTTPServer(('0.0.0.0', API_PORT), BytefenseAPIHandler)
    print(f"🚀 Bytefense API server running on port {API_PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API server")
        server.shutdown()