# Port Configuration Summary

## ✅ **Updated Configuration**

### Backend Servers:
- **main.py**: Port 8000 (Primary server with all features)
- **simple_main.py**: Port 8001 (Lightweight server for testing)
- **main_pdf_test.py**: Port 8002 (PDF testing only)

### Frontend:
- **Next.js Frontend**: Port 3000
- **API Connections**: Points to `http://localhost:8000` (main.py backend)

### CORS Configuration:
All backend servers now allow connections from:
- `http://localhost:3000` (Primary frontend port)
- `http://127.0.0.1:3000` (Alternative localhost format)

Removed port 3001 references as requested.

## 🚀 **How to Run**

### Start Backend (Primary):
```bash
cd /Users/wilson/Downloads/investment-portfolio-agent-main/backend
python3 main.py
# Server available at: http://localhost:8000
```

### Start Frontend:
```bash
cd /Users/wilson/Downloads/investment-portfolio-agent-main/frontend  
npm run dev
# Frontend available at: http://localhost:3000
```

### Alternative Backend Options:
```bash
# Lightweight server
python3 simple_main.py      # Port 8001

# PDF test server  
python3 main_pdf_test.py     # Port 8002
```

## 🔗 **Connection Flow**
Frontend (Port 3000) → Backend (Port 8000)

## ✅ **Test Endpoints**

### Backend Health Check:
```bash
curl http://localhost:8000/api/health
```

### PDF Generation Test:
```bash
curl http://localhost:8000/api/test-pdf
```

### Frontend:
```
http://localhost:3000
```

## 📋 **Configuration Complete**

✅ Backend: Port 8000  
✅ Frontend: Port 3000  
✅ CORS: Properly configured  
✅ PDF Generation: Working  
✅ API Connections: Aligned  

The system is now properly configured with consistent port usage! 🎉