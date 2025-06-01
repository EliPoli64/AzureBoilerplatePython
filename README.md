# Voto Pura Vida - API Serverless en Python

Este proyecto es una implementación local de un API serverless desarrollado en Python. El sistema gestiona funciones críticas de un sistema de votación electrónica y crowdfunding, utilizando procedimientos almacenados (Stored Procedures) y ORM (SQLAlchemy) sobre SQL Server. 

El enfoque está alineado con tecnologías cloud (como AWS Lambda o Azure Functions), pero el despliegue es 100% local para facilitar la colaboración y portabilidad entre desarrolladores.

## Estructura del Proyecto

```
APIs/
├── CS/                     # Versión original en C# (para referencia)
├── PY/                     # API actual implementada en Python
│   ├── app/                # Código fuente de la API
│   │   ├── main.py         # Punto de entrada con FastAPI
│   │   ├── database.py     # Conexión asíncrona y modelo base
│   │   ├── models.py       # Declaración de modelos ORM
│   │   ├── schemas.py      # Esquemas Pydantic
│   │   ├── crud/           # Funciones ORM
│   │   ├── stored_procedures.py  # Llamadas a SPs vía pyodbc
│   │   └── routers/        # Archivos de endpoints separados por tipo
│   ├── tests/              # Pruebas automatizadas
│   └── .env                # Variables de entorno (no subir al repo)
```

## Requisitos

- Python 3.10+
- SQL Server 2019 o superior
- Controlador ODBC para SQL Server
- `pyodbc`, `SQLAlchemy`, `FastAPI`, `uvicorn`, `python-dotenv`

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/Caso3Bases.git
cd Caso3Bases/APIs/PY
```

2. Crea y activa un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Crea un archivo `.env` en `APIs/PY/` con el siguiente contenido:

```ini
SqlConnectionString=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=VotoPuraVida;UID=sa;PWD=tu_password_segura
```

5. Ejecuta las migraciones iniciales (si se incluyen):

```bash
alembic upgrade head  # si usas Alembic para migraciones
```

## Ejecución local

```bash
uvicorn app.main:app --reload
```

La API estará disponible en:

```
http://localhost:8000
```

La documentación generada estará en:

```
http://localhost:8000/docs
```

## Endpoints implementados

### Con procedimientos almacenados (Stored Procedures)

- `POST /sp/crearActualizarPropuesta`
- `POST /sp/revisarPropuesta`
- `POST /sp/invertir`
- `POST /sp/repartirDividendos`

### Con ORM

- `POST /orm/votar`
- `POST /orm/comentar`
- `GET  /orm/listarVotos`
- `POST /orm/configurarVotacion`

Cada uno de estos endpoints ejecuta validaciones, transacciones y lógica de seguridad tal como se detalla en los requisitos del prototipo.

## Seguridad

- Validación de identidad por tokens o JWT
- Autenticación multifactor (MFA) en endpoints críticos
- Cifrado de votos y documentos sensibles
- Validaciones de rol, permisos y trazabilidad en todos los endpoints

## Base de Datos

La base de datos SQL Server debe contener:
- Procedimientos almacenados documentados en `scripts/sql/`
- Tablas normalizadas y relaciones según el diseño
- Historial de cambios, control de estados y bitácoras

## Scripts útiles

```bash
python scripts/test_connection.py

pytest tests/
```

## Integración con IA

Se dejan estructuras preparadas para validación por LLMs o clasificadores automáticos (por ejemplo, `reviewPayload`), especialmente en endpoints como `revisarPropuesta` y `comentar`.

## Despliegue

Aunque la arquitectura es serverless, se ejecuta localmente para facilitar pruebas, colaboración y despliegue sin necesidad de servicios cloud externos.


