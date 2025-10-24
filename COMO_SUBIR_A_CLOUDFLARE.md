# 🚀 GUÍA PASO A PASO: SUBIR PROYECTO A CLOUDFLARE PAGES

## ✅ ANTES DE EMPEZAR - VERIFICAR QUE TODO ESTÉ LISTO

### Archivos que deben existir:

**Frontend:**
- ✅ `frontend/src/config/api.js` - Configuración de API
- ✅ `frontend/src/services/api.js` - Actualizado con variables de entorno
- ✅ `frontend/src/services/authService.js` - Actualizado con variables de entorno
- ✅ `frontend/.env.example` - Ejemplo de variables de entorno
- ✅ `frontend/public/_redirects` - Para Cloudflare Pages

**Backend:**
- ✅ `backend/app/config.py` - Configuración actualizada
- ✅ `backend/.env.example` - Ejemplo de variables de entorno
- ✅ `backend/Procfile` - Para Railway
- ✅ `backend/railway.json` - Configuración Railway
- ✅ `backend/migrate_to_postgres.py` - Script de migración
- ✅ `backend/requirements.txt` - Con gunicorn==21.2.0

---

## 🌐 PASO 1: CREAR CUENTA EN CLOUDFLARE

1. Ve a https://dash.cloudflare.com
2. Regístrate o inicia sesión
3. Ve a "Pages" en el menú lateral

---

## 📦 PASO 2: CREAR NUEVO PROYECTO EN CLOUDFLARE PAGES

### 2.1 Conectar a GitHub

1. Click en "Create a project"
2. Selecciona "Connect to Git"
3. Autoriza Cloudflare a acceder a tu GitHub
4. Selecciona tu repositorio `sistema-gestion-empresarial`

### 2.2 Configurar Build

Cloudflare te pedirá la configuración de build:

- **Framework preset**: Vite
- **Build command**: `npm run build`
- **Build output directory**: `dist`
- **Root directory**: `frontend`

---

## 🔧 PASO 3: CONFIGURAR VARIABLES DE ENTORNO

Antes de desplegar, ve a "Settings" → "Environment variables":

Agrega:

```env
VITE_API_URL=https://tu-app.up.railway.app
```

(Usa la URL de tu backend de Railway del Paso 3 en `DESPLIEGUE_PRODUCCION.md`)

---

## 🚀 PASO 4: DESPLEGAR

1. Click en "Save and Deploy"
2. Cloudflare construirá y desplegará tu frontend
3. Espera a que termine (2-5 minutos)
4. Cuando termine, verás una URL como: `https://tu-app.pages.dev`
5. **Copia esta URL**, la necesitarás para configurar CORS en Railway

---

## ✅ PASO 5: CONFIGURAR CORS EN RAILWAY

### 5.1 Actualizar Variable en Railway

Ahora que tienes la URL de Cloudflare Pages, actualiza Railway:

1. Ve a Railway → Tu proyecto → "Variables"
2. Actualiza `FRONTEND_URL`:

```env
FRONTEND_URL=https://tu-app.pages.dev
```

### 5.2 Redesplegar Backend

1. Railway redesplegará automáticamente
2. Espera a que termine

---

## 🎉 ¡LISTO! TU FRONTEND ESTÁ EN CLOUDFLARE PAGES

### URLs Importantes:

- **Frontend:** `https://tu-app.pages.dev`
- **Backend API:** `https://tu-app.up.railway.app`

---

## 📝 PRÓXIMOS PASOS

Ahora que tu frontend está en Cloudflare Pages, puedes:

1. **Verificar que el frontend funciona correctamente**
2. **Probar la integración con el backend**

---

## ❌ SOLUCIÓN DE PROBLEMAS

### Error: "Build failed" en Cloudflare Pages

**Causa**: El build del frontend falló.

**Solución**:
1. Verifica que `Build command` sea `npm run build`
2. Verifica que `Build output directory` sea `dist`
3. Verifica que `Root directory` sea `frontend`
4. Ve a "Deployments" → Click en el deployment → "View build log"
5. Lee el error y corrígelo

### Error: "404 Not Found" en rutas del frontend

**Causa**: Las rutas del frontend no funcionan en Cloudflare Pages.

**Solución**:
1. Verifica que el archivo `_redirects` esté en `frontend/public/`
2. Contenido debe ser: `/* /index.html 200`
3. Redeploya en Cloudflare Pages

---

## 📞 SOPORTE

Si tienes problemas:

1. Lee los mensajes de error completos
2. Busca el error en Google: `cloudflare pages [mensaje de error]`
3. Verifica que todas las variables de entorno están configuradas
4. Verifica tu conexión a internet

---

## ✅ CHECKLIST FINAL

Antes de continuar con el despliegue:

- [ ] Cloudflare Pages configurado
- [ ] Frontend desplegado (`npm run build` exitoso)
- [ ] URL de frontend copiada
- [ ] CORS configurado en Railway

---

**¡Tu frontend está listo y funcionando en Cloudflare Pages! 🚀**

**Siguiente paso:** Verifica la integración con el backend y realiza pruebas completas.
