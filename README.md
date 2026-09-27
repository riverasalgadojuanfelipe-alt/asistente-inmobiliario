# Homev

Asistente inmobiliario inteligente para Colombia (Cali, Medellín, Bogotá y Tuluá). Búsqueda en lenguaje natural con recomendaciones justificadas por IA. Soporta operaciones de **compra** y **arriendo**.

## Producción

- **App:** https://www.homev.casa (apex https://homev.casa redirige a www)
- **URL de Vercel:** https://asistente-inmobiliario-snowy.vercel.app
- **API:** https://asistente-inmobiliario-api.onrender.com

Guía completa de despliegue en [`DEPLOY.md`](./DEPLOY.md).

## Estructura

```
asistente-inmobiliario/
└── backend/
    ├── app/
    │   ├── core/          # configuración y conexión a DB
    │   ├── models/        # modelos SQLAlchemy
    │   ├── schemas/       # esquemas Pydantic
    │   ├── services/      # lógica de negocio
    │   ├── routes/        # endpoints FastAPI
    │   └── main.py        # entrada de la app
    ├── requirements.txt
    ├── .env.example
    └── .gitignore
```

## Puesta en marcha (local)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Editar .env con la connection string de Supabase

uvicorn app.main:app --reload
```

Servidor local: http://localhost:8000
Docs interactivos: http://localhost:8000/docs

## Configuración Supabase

En `.env` usa la connection string de Postgres de Supabase:

```
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROYECTO.supabase.co:5432/postgres
```

## Endpoints

- `GET  /health` — health check
- `POST /api/v1/propiedades` — crear propiedad
- `GET  /api/v1/propiedades` — listar/filtrar (ciudad, tipo_operacion, precio_min/max, habitaciones_min, banos_min, area_min, barrio)
- `GET  /api/v1/propiedades/{id}` — obtener por id

## Ciudades soportadas

`cali`, `medellin`, `bogota`, `tulua`

## Tipos de operación

`venta`, `arriendo`
