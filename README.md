# VotoPuraVida – Azure Functions Boilerplate

Boilerplate para una API **serverless** escrita en Python y desplegada en Azure Functions. Incluye conexión segura a **Azure SQL Database** y dos funciones de ejemplo:

* **GET /status** – Verifica la salud del servicio.
* **POST /records** – Inserta un registro en la tabla `pv_infoIA`.

## Prerrequisitos

| Herramienta | Versión mínima |
|-------------|---------------|
| Python      | 3.11          |
| Azure CLI   | 2.60          |
| Azure Functions Core Tools | 4.x |
| ODBC Driver | 18 para SQL Server |

Instala Core Tools (Windows ➜ MSI, macOS/Linux ➜ npm):
```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

## Configuración local

1. **Clona el repo** y navega al directorio raíz.
2. Crea un entorno virtual y activa:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Copia `local.settings.json` > `local.settings.json.user` y rellena `SqlConnectionString`.
5. Inicia la función local:
   ```bash
   func start
   ```
6. Prueba:
   ```bash
    curl -X POST http://localhost:7071/api/records \
        -H "Content-Type: application/json" \
        -d '{
              "infoId": 1,
              "modeloIA": "gpt-4o",
              "apiKey": "sk-XXXX",
              "token": "someAuthToken",
              "maxTokens": 4096
            }'
   ```

## Despliegue en Azure

1. Inicia sesión y selecciona el subscription:
   ```bash
   az login
   az account set --subscription "<SUB_ID>"
   ```
2. Crea recursos (Grupo, Plan de Consumo, Function App y Azure SQL):
   ```bash
   az group create --name VotoPuraVidaRG --location eastus
   az storage account create --name votopuravidastor --location eastus --resource-group VotoPuraVidaRG --sku Standard_LRS
   az functionapp create --resource-group VotoPuraVidaRG --consumption-plan-location eastus \
      --runtime python --functions-version 4 --name VotoPuraVidaApi \
      --storage-account votopuravidastor
   az sql server create --name votopuravidasqlsrv --resource-group VotoPuraVidaRG --location eastus \
      --admin-user sqladmin --admin-password "<StrongPass123>"
   az sql db create --resource-group VotoPuraVidaRG --server votopuravidasqlsrv --name VotoPuraVidaDB --service-objective S0
   ```
3. Configura la cadena de conexión en la Function App:
   ```bash
   az functionapp config appsettings set --name VotoPuraVidaApi --resource-group VotoPuraVidaRG \
      --settings "SqlConnectionString=Driver={ODBC Driver 18 for SQL Server};Server=tcp:votopuravidasqlsrv.database.windows.net,1433;Database=VotoPV;Uid=sqladmin;Pwd=<StrongPass123>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
   ```
4. Publica el código:
   ```bash
   func azure functionapp publish VotoPuraVidaApi --python
   ```
5. Verifica endpoints:
   ```bash
   curl https://VotoPuraVidaApi.azurewebsites.net/api/status
   ```

## Capas compartidas

La carpeta `SharedLayer` actúa como **capa** de utilidades comunes (por ejemplo, `DbConnector`). Simplemente importa desde cualquier función:
```python
from SharedLayer.DbConnector import DbConnector
```


