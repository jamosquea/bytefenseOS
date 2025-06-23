class BytefenseDemo {
    constructor() {
        this.isRunning = false;
        this.threatsBlocked = 0;
        this.connectedUsers = 12;
        this.performance = 98;
        this.logEntries = [];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initCharts();
        this.startBackgroundActivity();
    }
    
    bindEvents() {
        document.getElementById('startDemo').addEventListener('click', () => this.startDemo());
        document.getElementById('resetDemo').addEventListener('click', () => this.resetDemo());
        
        document.querySelectorAll('.attack-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const attackType = e.currentTarget.dataset.attack;
                this.simulateAttack(attackType);
            });
        });
    }
    
    startDemo() {
        this.isRunning = true;
        this.addLogEntry('info', 'Demo iniciada - Monitoreo activo');
        document.getElementById('startDemo').disabled = true;
        
        // Simular actividad normal
        this.simulateNormalActivity();
    }
    
    resetDemo() {
        this.isRunning = false;
        this.threatsBlocked = 0;
        this.connectedUsers = 12;
        this.performance = 98;
        this.logEntries = [];
        
        this.updateUI();
        this.clearLog();
        this.addLogEntry('info', 'Demo reiniciada');
        
        document.getElementById('startDemo').disabled = false;
    }
    
    simulateAttack(type) {
        if (!this.isRunning) {
            this.addLogEntry('warning', 'Inicia la demo primero');
            return;
        }
        
        const attacks = {
            ddos: {
                name: 'Ataque DDoS',
                severity: 'high',
                duration: 3000,
                description: 'Múltiples conexiones maliciosas detectadas'
            },
            malware: {
                name: 'Malware',
                severity: 'critical',
                duration: 2000,
                description: 'Archivo malicioso bloqueado'
            },
            bruteforce: {
                name: 'Fuerza Bruta',
                severity: 'medium',
                duration: 4000,
                description: 'Intentos de login sospechosos'
            },
            phishing: {
                name: 'Phishing',
                severity: 'high',
                duration: 2500,
                description: 'Dominio malicioso bloqueado'
            }
        };
        
        const attack = attacks[type];
        
        // Mostrar ataque detectado
        this.addLogEntry('danger', `🚨 ${attack.name} detectado: ${attack.description}`);
        
        // Simular respuesta del sistema
        setTimeout(() => {
            this.threatsBlocked++;
            this.addLogEntry('success', `✅ ${attack.name} bloqueado automáticamente`);
            this.updateUI();
            
            // Actualizar gráficos
            this.updateThreatChart(type);
        }, 1000);
        
        // Restaurar estado normal
        setTimeout(() => {
            this.addLogEntry('info', 'Sistema estabilizado - Monitoreo continuo');
        }, attack.duration);
    }
    
    simulateNormalActivity() {
        if (!this.isRunning) return;
        
        // Actividad aleatoria cada 3-8 segundos
        const interval = Math.random() * 5000 + 3000;
        
        setTimeout(() => {
            const activities = [
                'Usuario conectado via VPN',
                'Actualización de reglas de firewall',
                'Escaneo de red completado',
                'Backup automático realizado',
                'Certificados SSL renovados'
            ];
            
            const activity = activities[Math.floor(Math.random() * activities.length)];
            this.addLogEntry('info', activity);
            
            // Pequeñas variaciones en métricas
            this.connectedUsers += Math.floor(Math.random() * 3) - 1;
            this.performance += Math.floor(Math.random() * 3) - 1;
            
            // Mantener valores en rangos realistas
            this.connectedUsers = Math.max(8, Math.min(25, this.connectedUsers));
            this.performance = Math.max(95, Math.min(100, this.performance));
            
            this.updateUI();
            this.simulateNormalActivity();
        }, interval);
    }
    
    addLogEntry(type, message) {
        const timestamp = new Date().toLocaleTimeString();
        const entry = { type, message, timestamp };
        
        this.logEntries.unshift(entry);
        
        // Mantener solo las últimas 20 entradas
        if (this.logEntries.length > 20) {
            this.logEntries.pop();
        }
        
        this.updateLog();
    }
    
    updateLog() {
        const container = document.getElementById('logContainer');
        container.innerHTML = '';
        
        this.logEntries.forEach(entry => {
            const div = document.createElement('div');
            div.className = `log-entry ${entry.type}`;
            div.innerHTML = `
                <span class="timestamp">${entry.timestamp}</span>
                <span class="message">${entry.message}</span>
            `;
            container.appendChild(div);
        });
    }
    
    clearLog() {
        document.getElementById('logContainer').innerHTML = '';
    }
    
    updateUI() {
        document.getElementById('threatsBlocked').textContent = this.threatsBlocked;
        document.getElementById('connectedUsers').textContent = this.connectedUsers;
        document.getElementById('performance').textContent = this.performance + '%';
        
        // Actualizar estado del sistema
        const statusElement = document.getElementById('systemStatus');
        if (this.performance > 95) {
            statusElement.textContent = 'PROTEGIDO';
            statusElement.className = 'status-value protected';
        } else if (this.performance > 90) {
            statusElement.textContent = 'ALERTA';
            statusElement.className = 'status-value warning';
        } else {
            statusElement.textContent = 'CRÍTICO';
            statusElement.className = 'status-value danger';
        }
    }
    
    initCharts() {
        // Inicializar gráficos (implementación en charts.js)
        if (window.initTrafficChart) {
            window.initTrafficChart();
        }
        if (window.initThreatChart) {
            window.initThreatChart();
        }
    }
    
    updateThreatChart(threatType) {
        if (window.updateThreatChart) {
            window.updateThreatChart(threatType);
        }
    }
    
    startBackgroundActivity() {
        // Actividad de fondo para hacer la demo más realista
        setInterval(() => {
            if (this.isRunning) {
                // Actualizar gráfico de tráfico
                if (window.updateTrafficChart) {
                    window.updateTrafficChart();
                }
            }
        }, 2000);
    }
}

// Inicializar demo cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    new BytefenseDemo();
});