# ShipInvoice RD API

Backend de facturacion construido con FastAPI, SQLAlchemy y Alembic.

## Tecnologias

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Docker Compose (para base de datos local)

## Estructura del proyecto

```text
.
|-- alembic/
|-- common/
|-- config/
|-- controllers/
|-- db/
|-- repositories/
|-- routers/
|-- services/
|-- tests/
`-- main.py
```

## Variables de entorno

Crear un archivo `.env` en la raiz del proyecto:

```env
DATABASE_URL=postgresql+psycopg://shipinvoice:shipinvoice@localhost:5433/shipinvoice
```

## Levantar servicios de infraestructura

Este proyecto incluye `docker-compose.yml` con PostgreSQL y pgAdmin.

```bash
docker compose up -d
```

Servicios expuestos:

- PostgreSQL: `localhost:5433`
- pgAdmin: `http://localhost:5050`

Credenciales por defecto (definidas en `docker-compose.yml`):

- DB user: `shipinvoice`
- DB password: `shipinvoice`
- DB name: `shipinvoice`
- pgAdmin user: `admin@shipinvoice.local`
- pgAdmin password: `admin123`

## Instalacion local

1. Crear y activar entorno virtual:

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

2. Instalar dependencias principales:

```bash
pip install fastapi uvicorn sqlalchemy alembic psycopg python-dotenv pydantic[email]
```

> Si ya tienes un archivo de dependencias en otro branch o entorno, puedes usarlo en lugar de este comando.

## Migraciones (Alembic)

Aplicar migraciones pendientes:

```bash
alembic upgrade head
```

Crear una nueva migracion:

```bash
alembic revision --autogenerate -m "descripcion"
```

## Ejecutar la API

```bash
uvicorn main:app --reload
```

La API queda disponible en:

- Base URL: `http://127.0.0.1:8000`
- Docs Swagger: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/health`

## Endpoints actuales

Prefijo global: `/api`

- `GET /api/clients` - Lista clientes
- `POST /api/clients` - Crea un cliente

Ejemplo de body para crear cliente:

```json
{
  "name": "Empresa Demo SRL",
  "phone": "809-555-1212",
  "email": "contacto@demo.com",
  "document_type": "RNC",
  "document_number": "131234567",
  "address_rd": "Santo Domingo, RD",
  "notes": "Cliente de prueba"
}
```

## Pruebas

Si tienes `pytest` configurado en tu entorno:

```bash
pytest
```

## Notas

- El nombre del proyecto en FastAPI es `ShipInvoice RD API`.
- El prefijo de rutas configurado es `/api`.
