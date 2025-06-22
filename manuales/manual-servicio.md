# ⚙️ Manual de Servicio - Bytefense OS 
 
## 🔧 Configuración de Servicios 
 
### Servicios Systemd 
 
Bytefense OS utiliza varios servicios systemd: 
 
- `bytefense-api.service` - API REST principal 
- `bytefense-watch.service` - Monitor de amenazas 
- `bytefense-alerts.service` - Sistema de alertas 
- `bytefense-dashboard.service` - Panel web 
 
### Comandos de Gestión 
 
```bash 
# Iniciar servicios 
sudo systemctl start bytefense-api 
sudo systemctl start bytefense-watch 
 
# Habilitar en arranque 
sudo systemctl enable bytefense-api 
sudo systemctl enable bytefense-watch 
 
# Ver estado 
sudo systemctl status bytefense-* 
``` 
