#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bytefense OS - Motor de IA para Detección de Amenazas
"""

import numpy as np
import sqlite3
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib

class AIThreatDetector:
    def __init__(self):
        self.db_path = '/opt/bytefense/intel/threats.db'
        self.model_path = '/opt/bytefense/ai/models/'
        self.models = {}
        self.scalers = {}
        self.feature_cache = deque(maxlen=1000)
        self.running = True
        
        # Crear directorio de modelos
        os.makedirs(self.model_path, exist_ok=True)
        
        # Inicializar modelos
        self.initialize_models()
        
        # Iniciar threads de análisis
        self.start_analysis_threads()
    
    def initialize_models(self):
        """Inicializar modelos de IA"""
        # Modelo para detección de anomalías en tráfico de red
        self.models['network_anomaly'] = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        # Modelo para clustering de ataques
        self.models['attack_clustering'] = DBSCAN(
            eps=0.5,
            min_samples=5
        )
        
        # Escaladores para normalización
        self.scalers['network'] = StandardScaler()
        self.scalers['behavior'] = StandardScaler()
        
        # Cargar modelos entrenados si existen
        self.load_trained_models()
    
    def load_trained_models(self):
        """Cargar modelos previamente entrenados"""
        try:
            network_model_file = os.path.join(self.model_path, 'network_anomaly.pkl')
            if os.path.exists(network_model_file):
                self.models['network_anomaly'] = joblib.load(network_model_file)
                print("[AI] Modelo de anomalías de red cargado")
            
            scaler_file = os.path.join(self.model_path, 'network_scaler.pkl')
            if os.path.exists(scaler_file):
                self.scalers['network'] = joblib.load(scaler_file)
                print("[AI] Escalador de red cargado")
                
        except Exception as e:
            print(f"[AI] Error cargando modelos: {e}")
    
    def save_models(self):
        """Guardar modelos entrenados"""
        try:
            joblib.dump(
                self.models['network_anomaly'], 
                os.path.join(self.model_path, 'network_anomaly.pkl')
            )
            joblib.dump(
                self.scalers['network'], 
                os.path.join(self.model_path, 'network_scaler.pkl')
            )
            print("[AI] Modelos guardados exitosamente")
            
        except Exception as e:
            print(f"[AI] Error guardando modelos: {e}")
    
    def extract_network_features(self, events):
        """Extraer características de eventos de red"""
        features = []
        
        for event in events:
            try:
                # Características básicas
                feature_vector = [
                    len(event.get('source_ip', '')),  # Longitud de IP
                    event.get('port', 0),  # Puerto
                    len(event.get('description', '')),  # Longitud de descripción
                    event.get('severity', 1),  # Severidad
                ]
                
                # Características temporales
                event_time = datetime.fromisoformat(event.get('date', datetime.now().isoformat()))
                hour = event_time.hour
                day_of_week = event_time.weekday()
                
                feature_vector.extend([
                    hour,
                    day_of_week,
                    1