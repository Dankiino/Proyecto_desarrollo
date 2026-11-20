# Servicio de Comercio

Servicio Django responsable de las operaciones de carrito y checkout. Usa
PostgreSQL (`comercio_db`) y consulta productos en MongoDB Atlas
(`catalogo_db`).

## Configuración local en Windows

Desde CMD, ubicado en `comercio-service`:

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
```

Si usas PowerShell y aparece un error indicando que la ejecución de scripts está
bloqueada, permite la activación solo en esa terminal y activa el entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

El cambio de política termina al cerrar esa terminal. En CMD, usa
`venv\Scripts\activate.bat` como en los comandos de configuración.

Completa `.env` con los valores privados del equipo:

- `COMERCIO_DATABASE_URL`: conexión PostgreSQL de Comercio.
- `CATALOGO_MONGO_URI`: conexión a MongoDB Atlas.
- `JWT_SIGNING_KEY`: debe ser exactamente la misma clave configurada en Gestión.

No uses las credenciales de ejemplo como valores reales ni compartas el archivo
`.env`.

## Migraciones e inicio

```cmd
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

La API local queda disponible bajo `http://127.0.0.1:8001/api/`.

Para desarrollo local, CORS permite los orígenes de Vite
`http://localhost:5173` y `http://127.0.0.1:5173`.

## Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/carrito/calcular` | Calcula el carrito con productos del catálogo |
| POST | `/api/checkout` | Procesa la solicitud de checkout autenticada |

El checkout requiere un JWT válido emitido por Gestión y la cabecera
`Idempotency-Key`. Consulta los contratos y validaciones del código antes de
integrar un cliente.
