# 🔧 Manual de Mantenimiento - Bytefense OS 
 
## 💾 Procedimientos de Backup 
 
### Backup de Base de Datos 
 
```bash 
# Backup manual 
sudo sqlite3 /opt/bytefense/system/bytefense.db ".backup /backup/bytefense-$(date +%Y%m%d).db" 
 
# Backup automático (cron) 
echo "0 2 * * * root sqlite3 /opt/bytefense/system/bytefense.db '.backup /backup/bytefense-$(date +%Y%m%d).db'" | sudo tee -a /etc/crontab 
``` 
 
### Backup de Configuración 
 
```bash 
# Backup completo de configuración 
sudo tar -czf /backup/bytefense-config-$(date +%Y%m%d).tar.gz /opt/bytefense/system/ 
``` 
