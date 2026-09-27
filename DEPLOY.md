# Despliegue — Guía paso a paso (100% capa gratuita)

Este proyecto se despliega en **dos plataformas**:
- **Render** → backend FastAPI (`backend/`)
- **Vercel** → frontend Next.js (`frontend/`)
- **Supabase** → base de datos Postgres (ya la tienes)

Todo se mantiene en el free tier. Caveats importantes al final.

---

## 1. Backend en Render

### 1.1 Crear cuenta y conectar el repo
1. Entra a https://render.com y regístrate con tu cuenta de GitHub (`riverasalgadojuanfelipe-alt`).
2. Autoriza a Render a leer el repo `asistente-inmobiliario`.

### 1.2 Crear el servicio con el Blueprint
El repo ya trae [`render.yaml`](./render.yaml) en la raíz.

1. Dashboard → **New +** → **Blueprint**.
2. Selecciona el repo `asistente-inmobiliario`.
3. Render detecta el `render.yaml` y muestra el servicio `asistente-inmobiliario-api`.
4. **Antes de "Apply"**, te va a pedir los secretos marcados como `sync: false`:
   - `DATABASE_URL` → pega el mismo que tienes en `backend/.env` (Supabase pooler URI).
   - `GEMINI_API_KEY` → pega la key de https://aistudio.google.com/app/apikey.
5. Click **Apply**. Render clona, instala, corre `alembic upgrade head` y levanta uvicorn.

El primer build tarda ~3-5 min. Cuando termine, Render te da una URL tipo:
```
https://asistente-inmobiliario-api.onrender.com
```
Verifica con:
```
https://asistente-inmobiliario-api.onrender.com/health
→ {"status":"healthy"}
```

### 1.3 Variables de entorno (referencia)
Ya quedan configuradas por el blueprint, pero podés cambiarlas en
Dashboard → tu servicio → **Environment**:

| Var | Valor | Notas |
|---|---|---|
| `PYTHON_VERSION` | `3.12.7` | El código usa sintaxis 3.10+ |
| `DATABASE_URL` | (secreto) | Supabase URI |
| `GEMINI_API_KEY` | (secreto) | Free tier |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Cambiar aquí si Google deprecia |
| `CORS_ORIGINS` | `*` inicialmente → luego la URL de Vercel | Ver paso 3 |

---

## 2. Frontend en Vercel

### 2.1 Crear cuenta y conectar el repo
1. Entra a https://vercel.com/signup y regístrate con GitHub (`riverasalgadojuanfelipe-alt`).
2. Autoriza a Vercel al repo `asistente-inmobiliario`.

### 2.2 Importar el proyecto
1. Dashboard → **Add New** → **Project** → importa `asistente-inmobiliario`.
2. En "Configure Project":
   - **Root Directory:** `frontend` (Vercel debe apuntar al subdirectorio, no a la raíz).
   - **Framework Preset:** Next.js (autodetectado).
   - **Build/Install/Output commands:** deja los defaults.
3. Expandí **Environment Variables** y agregá:
   - `NEXT_PUBLIC_API_URL` = `https://asistente-inmobiliario-api.onrender.com`
     (sin `/api/v1`, sin trailing slash — el código lo agrega).
4. Click **Deploy**.

Al minuto tenés una URL tipo `https://asistente-inmobiliario.vercel.app` (o `-git-main-<user>.vercel.app` para previews). Abrí y probá.

---

## 3. Cerrar CORS en el backend (recomendado tras el primer deploy)
Una vez sepas tu URL de Vercel, volvé a Render → tu servicio → **Environment**:

1. Editá `CORS_ORIGINS` de `*` a algo como:
   ```
   https://asistente-inmobiliario.vercel.app,https://asistente-inmobiliario-git-main-<user>.vercel.app
   ```
   (Incluí también el dominio de previews de PR si querés que funcionen ahí.)
2. Guardá — Render reinicia solo (~30s).

Con esto, solo tu frontend puede llamar al backend.

---

## 4. Cosas que quedan en tu maquina local
Nada cambia. `backend/.env` y `frontend/.env.local` siguen mandando en desarrollo:
- Backend local: `.env` con `DATABASE_URL`, `GEMINI_API_KEY`, `CORS_ORIGINS=*`.
- Frontend local: `.env.local` con `NEXT_PUBLIC_API_URL=http://localhost:8000`.

Los `.env*` siguen gitignoreados.

---

## 5. Caveats del free tier (léelos, van a pasar)

**Render free:**
- Se apaga tras **15 min sin tráfico**. El siguiente request tarda **~30-60s** en despertar (verás el "Analizando el mercado…" del frontend durante ese cold start).
- 512MB RAM, 750h/mes gratis (suficiente si es la única app).
- Si molesta el cold start, se resuelve con cualquier plan pago ($7/mes).

**Vercel free:**
- Sin cold starts para páginas estáticas / SSR liviano — todo fluido.
- 100GB banda/mes; ilimitado en el plan Hobby para uso personal.

**Supabase free:**
- La DB **se pausa** si el proyecto está inactivo ~7 días. Al primer request se despierta (varios segundos). No pierdes datos.

**Gemini free:**
- Cuota por modelo por día. `gemini-flash-lite-latest` es la opción más generosa. Con 1 llamada por búsqueda (ya optimizado), estimo ~1000+ búsquedas/día en free tier antes de topear.

---

## 6. Cómo actualizar
Cada push a `main`:
- Render detecta cambios en `backend/` (o el `render.yaml`) → rebuild automático.
- Vercel detecta cambios en `frontend/` → deploy automático.

No hay que hacer nada más. Alembic corre en cada arranque (`alembic upgrade head` es idempotente), así que las migraciones nuevas se aplican solas.

---

## 7. Troubleshooting rápido
- **502 desde el frontend:** probablemente Render cold-start. Refresh en ~30s.
- **CORS error en el navegador:** revisá que `CORS_ORIGINS` en Render incluya tu URL exacta de Vercel (con `https://`, sin trailing slash).
- **429 "Se agotó la cuota":** el mensaje real de Gemini. Esperá al reset del día (00:00 PT) o cambiá `GEMINI_MODEL` a otro que aún tenga cuota — la cuota es por modelo.
- **500 en `/api/v1/buscar`:** revisá los logs de Render (Dashboard → tu servicio → **Logs**).
