# SyncCreate Service Connection Issues - Troubleshooting Guide

## Problem
`Unable to connect to http://localhost:8084/health`

## Root Cause
Docker Desktop is not running or not installed.

---

## Solution

### Step 1: Start Docker Desktop
1. Open **Windows Start Menu**
2. Search for **"Docker Desktop"**
3. Click to launch it
4. Wait 30-60 seconds for Docker daemon to start (you'll see the whale icon in taskbar)

### Step 2: Verify Docker is Running
```powershell
docker --version
docker ps
```

Both commands should complete successfully without errors.

### Step 3: Build and Start Services
```powershell
# Navigate to repo
cd C:\Users\USER\Documents\KIKI

# Option A: Use quick-start script (automated)
.\quick-start.ps1

# Option B: Manual start
docker-compose build synccreate
docker-compose up -d synccreate

# Wait 30 seconds for service to start
Start-Sleep -Seconds 30

# Test
curl http://localhost:8084/health
```

### Step 4: Verify All Services Running
```powershell
docker-compose ps
```

Expected output:
```
NAME           STATUS        PORTS
redis          Up            0.0.0.0:6379->6379/tcp
syncvalue      Up            0.0.0.0:50051->50051/tcp
syncshield     Up            0.0.0.0:8081->8081/tcp
syncengage     Up            0.0.0.0:8083->8083/tcp
synccreate     Up            0.0.0.0:8084->8084/tcp
syncflow       Up
```

---

## If Issues Persist

### Check Docker Daemon Logs
```powershell
# Check if Docker Desktop has any errors
# Settings → Resources → CPU/Memory allocation
# Ensure: CPU ≥2, RAM ≥4GB, Disk ≥10GB free
```

### Restart Docker Completely
```powershell
# Stop all containers
docker-compose down

# Wait 10 seconds
Start-Sleep -Seconds 10

# Close Docker Desktop completely (right-click tray icon → Quit)
# Reopen Docker Desktop
# Wait for daemon to start
# Restart services
docker-compose up -d
```

### Check Port Conflicts
```powershell
# See what's using port 8084
netstat -ano | findstr :8084

# If something is using it:
# Option 1: Kill the process
taskkill /PID <PID> /F

# Option 2: Use different port (edit docker-compose.yml)
# ports:
#   - "8085:8084"
```

### View SyncCreate Logs
```powershell
# See detailed error messages
docker-compose logs synccreate

# Follow logs in real-time
docker-compose logs -f synccreate
```

---

## Quick Checklist

- [ ] Docker Desktop installed (https://www.docker.com/products/docker-desktop)
- [ ] Docker Desktop is running (check taskbar)
- [ ] `docker ps` returns successfully
- [ ] `docker-compose version` returns v2.x or higher
- [ ] Ran `docker-compose build synccreate`
- [ ] Ran `docker-compose up -d synccreate`
- [ ] Waited 30+ seconds for startup
- [ ] Port 8084 is not blocked by firewall
- [ ] Machine has ≥4GB free RAM
- [ ] Machine has ≥10GB free disk space

---

## Expected Timeline

1. **Docker Desktop launch:** 30-60 seconds
2. **Image build:** 2-5 minutes (first time only)
3. **Container start:** 5-10 seconds
4. **Service ready:** 30 seconds total from `docker-compose up`

---

## Still Not Working?

Try the nuclear option:
```powershell
# Stop everything
docker-compose down -v

# Remove all Docker resources
docker system prune -a --volumes -f

# Close Docker Desktop completely
# Reopen Docker Desktop
# Wait 60 seconds
# Rebuild
docker-compose build --no-cache synccreate
docker-compose up -d
```

Then wait 60 seconds and try:
```powershell
curl http://localhost:8084/health
```
