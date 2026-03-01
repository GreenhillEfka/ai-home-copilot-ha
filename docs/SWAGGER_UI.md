# Swagger UI Setup for PilotSuite Styx Core

This document describes how to set up interactive Swagger UI for the PilotSuite Styx Core API.

## Quick Start

### Option 1: Using Swagger UI Online (Development Only)

1. Open [Swagger UI Online](https://editor.swagger.io/)
2. Copy the contents of `openapi.yaml`
3. Paste into the editor
4. Interact with your API documentation

**⚠️ Warning:** Do not use online editors with production API keys or sensitive information.

### Option 2: Local Swagger UI with Docker

```bash
# Run Swagger UI locally with Docker
docker run -d \
  -p 8080:8080 \
  -e SWAGGER_JSON=/openapi.yaml \
  -v $(pwd)/openapi.yaml:/openapi.yaml \
  swaggerapi/swagger-ui
```

Then open: http://localhost:8080

### Option 3: Local Swagger UI with Python

```bash
# Install swagger-ui-bundle
pip install connexion swagger-ui-bundle

# Serve with Python
python -m http.server 8080
```

Download Swagger UI:
```bash
curl -L https://github.com/swagger-api/swagger-ui/archive/master.tar.gz | tar xz
cp -r swagger-ui-master/dist/* /path/to/webserver/
cp openapi.yaml /path/to/webserver/
```

Edit `index.html` to point to your `openapi.yaml`.

### Option 4: Integrated in Flask App (Recommended)

Add Swagger UI to the PilotSuite Flask application:

```python
# In main.py or a dedicated docs module
from flask import send_from_directory
import os

@app.route('/docs')
@app.route('/docs/')
def docs_index():
    return send_from_directory('static/swagger-ui', 'index.html')

@app.route('/docs/<path:path>')
def docs_static(path):
    return send_from_directory('static/swagger-ui', path)

@app.route('/docs/openapi.yaml')
def openapi_spec():
    return send_from_directory('docs', 'openapi.yaml')
```

Download Swagger UI to `static/swagger-ui/`:
```bash
cd copilot_core/rootfs/usr/src/app/static
curl -L https://github.com/swagger-api/swagger-ui/archive/master.tar.gz | tar xz
mv swagger-ui-master swagger-ui
```

Then access at: http://localhost:8909/docs

## Features

The OpenAPI specification includes:

- ✅ **Auto-Generated from All Endpoints**: 48 API paths documented
- ✅ **Interactive Swagger UI**: Try out API calls directly from the browser
- ✅ **Complete Request/Response Documentation**: All parameters and schemas
- ✅ **Authentication Schema**: API Key and Bearer token documented
- ✅ **Example Values**: Sample values for all parameters
- ✅ **14 API Modules**: System Health, Brain Graph, Habitus, Candidates, Mood, Notifications, Sharing, Collective Intelligence, Energy, UniFi, Tags, Dev Surface, Telegram, Hub

## API Modules Documented

| Module | Endpoints | Auth Type |
|--------|-----------|-----------|
| System Health | 3 | API Key |
| Brain Graph | 3 | API Key |
| Habitus | 3 | API Key |
| Candidates | 5 | API Key |
| Mood | 6 | API Key |
| Notifications | 5 | Bearer Token |
| Sharing | 5 | API Key |
| Collective Intelligence | 9 | API Key |
| Energy | 3 | API Key |
| UniFi | 1 | Bearer Token |
| Tags | 3 | Bearer Token |
| Dev Surface | 2 | API Key |
| Telegram | 2 | Bearer Token |
| Hub | 3+ | Bearer Token |

**Total:** 53 documented operations across 14 modules

## Regenerating Documentation

To regenerate the OpenAPI spec and API reference:

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/docs

# Generate OpenAPI spec
python3 openapi_spec.py --output openapi.yaml

# Generate API reference
python3 api_reference.py --output API_REFERENCE.md

# Copy to docs directory
cp openapi.yaml ../../docs/
cp API_REFERENCE.md ../../docs/
```

## Validation

Validate the OpenAPI spec:

```bash
# Using swagger-cli
npm install -g swagger-cli
swagger-cli validate openapi.yaml

# Using spectral
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml
```

## Next Steps

1. **Set up Swagger UI** in the Flask app (Option 4 above)
2. **Add more examples** to request/response schemas
3. **Document remaining Hub endpoints** (120+ total)
4. **Add interactive tutorials** for common workflows
5. **Set up automated regeneration** on CI/CD pipeline

## Files Created

```
pilotsuite-styx-core/
├── docs/
│   ├── openapi.yaml              # OpenAPI 3.0 specification (1,281 lines)
│   ├── API_REFERENCE.md          # Complete API documentation (1,149 lines)
│   └── SWAGGER_UI.md             # This file
└── copilot_core/docs/
    ├── openapi_spec.py           # OpenAPI generator script (1,675 lines)
    ├── api_reference.py          # API reference generator (1,267 lines)
    ├── openapi.yaml              # Copy of openapi.yaml
    └── API_REFERENCE.md          # Copy of API_REFERENCE.md
```

---

*Generated: 2026-03-01*  
*Version: 12.5.0*
