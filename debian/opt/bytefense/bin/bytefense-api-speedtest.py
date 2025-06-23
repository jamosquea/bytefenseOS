#!/usr/bin/env python3
# API endpoints para SpeedTest

from flask import Flask, jsonify, request
from bytefense_speedtest import BytefenseSpeedTest

app = Flask(__name__)
speedtest = BytefenseSpeedTest()

@app.route('/api/speedtest/run', methods=['POST'])
def run_test():
    """Ejecutar prueba de velocidad"""
    result = speedtest.run_speedtest('manual')
    return jsonify(result)

@app.route('/api/speedtest/history', methods=['GET'])
def get_history():
    """Obtener historial de pruebas"""
    limit = request.args.get('limit', 24, type=int)
    results = speedtest.get_recent_results(limit)
    return jsonify(results)

@app.route('/api/speedtest/config', methods=['GET', 'POST'])
def manage_config():
    """Gestionar configuración"""
    if request.method == 'GET':
        return jsonify(speedtest.config)
    else:
        speedtest.config.update(request.json)
        speedtest.save_config()
        return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=False)