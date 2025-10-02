# Frontend Integration Test Setup

## 🎯 Backend + Frontend Integration Testing

Dieses Dokument beschreibt, wie Sie das Videoflix Backend mit dem offiziellen Frontend testen können.

## Voraussetzungen

### Backend (Ihr Django-Projekt)
- ✅ Backend läuft auf `http://localhost:8000`
- ✅ CORS für `localhost:5500` konfiguriert
- ✅ JWT HttpOnly Cookies implementiert
- ✅ Alle API-Endpunkte funktionsfähig

### Frontend (Offizielle Vorlage)
```bash
# 1. Frontend-Repository klonen
git clone https://github.com/Developer-Akademie-Backendkurs/project.Videoflix.git frontend-videoflix
cd frontend-videoflix

# 2. VS Code öffnen
code .

# 3. Live Server Extension installieren (falls noch nicht vorhanden)
# Extensions -> "Live Server" von Ritwick Dey installieren
```

## 🚀 Schritt-für-Schritt Setup

### 1. Backend starten

```bash
# In Ihrem Videoflix Backend-Ordner
cd C:\Users\engel\OneDrive\Desktop\Videoflix

# Docker-Variante (empfohlen)
docker-compose up -d

# Oder lokale Entwicklung
python manage.py runserver
```

**Verify Backend:**
- ✅ http://localhost:8000/admin/ erreichbar
- ✅ http://localhost:8000/api/video/ (erfordert Login)

### 2. Test-Daten erstellen

```bash
# Container-Variante
docker-compose exec web python manage.py shell

# Lokale Variante  
python manage.py shell
```

```python
# Test-User erstellen
from auth_app.models import CustomUser
from video_app.models import Video, Category

# Admin-User (falls noch nicht vorhanden)
admin = CustomUser.objects.create_user(
    email='admin@test.com',
    password='testpass123',
    is_active=True
)

# Test-User
user = CustomUser.objects.create_user(
    email='test@videoflix.com', 
    password='testpass123',
    is_active=True
)

# Kategorien erstellen (falls noch nicht vorhanden)
drama, _ = Category.objects.get_or_create(name='Drama')
action, _ = Category.objects.get_or_create(name='Action')
comedy, _ = Category.objects.get_or_create(name='Comedy')

print(f"Created users: {CustomUser.objects.count()}")
print(f"Categories: {Category.objects.count()}")
```

### 3. Frontend starten

```bash
# Im Frontend-Verzeichnis
cd frontend-videoflix

# VS Code öffnen
code .

# In VS Code:
# 1. Rechtsklick auf index.html
# 2. "Open with Live Server" wählen
# 3. Browser öffnet automatisch http://localhost:5500
```

### 4. Integration testen

#### Login-Test:
1. **Frontend öffnen:** http://localhost:5500
2. **Login-Seite navigieren**
3. **Test-Credentials eingeben:**
   - Email: `test@videoflix.com`
   - Passwort: `testpass123`
4. **Login durchführen**
5. **✅ Erwartung:** Weiterleitung zum Dashboard

#### API-Test via Browser DevTools:
```javascript
// Browser Console öffnen (F12)

// 1. Login testen
fetch('http://localhost:8000/api/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    email: 'test@videoflix.com',
    password: 'testpass123'
  })
})
.then(r => r.json())
.then(console.log);

// 2. Video-Liste abrufen (nach Login)
fetch('http://localhost:8000/api/video/', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log);
```

## 🔧 Fehlerbehebung

### CORS-Fehler
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:5500' has been blocked by CORS policy
```

**Lösung:** Backend CORS-Konfiguration prüfen:
```python
# In core/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",  # ← Muss vorhanden sein
    "http://127.0.0.1:5500",
]
CORS_ALLOW_CREDENTIALS = True  # ← Wichtig für Cookies
```

### Cookie-Probleme
```
Set-Cookie wurde ignoriert wegen SameSite-Attribut
```

**Lösung:** Cookie-Settings prüfen:
```python
# In auth_app/api/views.py
response.set_cookie(
    'access_token', str(access_token),
    httponly=True, 
    secure=False,    # ← Für localhost auf False
    samesite='Lax'   # ← Wichtig für Cross-Origin
)
```

### Video-Upload für Tests

Über Django Admin Testvideos hinzufügen:
1. **Admin öffnen:** http://localhost:8000/admin/
2. **Login:** admin@test.com / testpass123
3. **Videos → Add Video**
4. **Kleine Testdatei hochladen** (MP4, <50MB)
5. **HLS-Processing abwarten** (Check in Logs: `docker-compose logs -f worker`)

## 📋 Test-Checkliste

### ✅ Authentication Flow:
- [ ] Login mit gültigen Credentials
- [ ] Login mit ungültigen Credentials (Fehler)
- [ ] Logout funktioniert
- [ ] Token Refresh automatisch
- [ ] Registrierung + Email-Aktivierung
- [ ] Password Reset Flow

### ✅ Video Dashboard:
- [ ] Video-Liste wird geladen
- [ ] Thumbnails werden angezeigt
- [ ] Kategorien sind gruppiert
- [ ] Hero-Video wird hervorgehoben
- [ ] Video-Player startet
- [ ] HLS-Streaming funktioniert
- [ ] Auflösungen wechselbar

### ✅ API-Responses:
- [ ] JSON-Format korrekt
- [ ] HTTP-Status-Codes korrekt
- [ ] Fehlerbehandlung funktioniert
- [ ] CORS-Headers gesetzt
- [ ] Cookies werden gesetzt/gelesen

## 🎯 Debugging-Tools

### Backend-Logs verfolgen:
```bash
# Docker-Logs
docker-compose logs -f web
docker-compose logs -f worker

# Lokale Entwicklung
python manage.py runserver --verbosity=2
```

### Frontend Network-Tab:
1. **F12 → Network Tab**
2. **Preserve Log aktivieren**
3. **Frontend-Aktionen durchführen**
4. **API-Calls überprüfen:**
   - Status Codes
   - Request/Response Headers
   - Cookie-Transfer
   - Response Bodies

### API-Test mit Curl:
```bash
# Login
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@videoflix.com","password":"testpass123"}' \
  -c cookies.txt -v

# Video-API mit Cookies
curl http://localhost:8000/api/video/ \
  -b cookies.txt -v
```

## 🎉 Erfolgreicher Test

Bei erfolgreichem Test sollten Sie sehen:
- ✅ **Login:** Weiterleitung zum Dashboard
- ✅ **Videos:** Liste mit Thumbnails und Metadaten  
- ✅ **Player:** HLS-Streaming funktioniert
- ✅ **Auflösungen:** 480p, 720p, 1080p wechselbar
- ✅ **Navigation:** Logout, Kategorien, Hero-Video

Das Frontend ist vollständig kompatibel mit Ihrem Backend! 🚀