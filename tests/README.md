# Tests Documentation

این دایرکتوری شامل تست‌های خودکار برای پروژه است.

## ساختار تست‌ها

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures و تنظیمات Pytest
├── test_knowledge_base_routes.py  # تست‌های API routes
├── test_knowledge_base_service.py # تست‌های unit برای KnowledgeBaseService
├── test_company_document_service.py # تست‌های unit برای CompanyDocumentService
└── integration/
    └── test_knowledge_base_integration.py # تست‌های integration
```

## اجرای تست‌ها

### نصب وابستگی‌ها

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio httpx
```

### اجرای تمام تست‌ها

```bash
pytest
```

### اجرای تست‌های خاص

```bash
# فقط تست‌های unit
pytest -m "not integration"

# فقط تست‌های integration
pytest -m integration

# یک فایل خاص
pytest tests/test_knowledge_base_routes.py

# یک تست خاص
pytest tests/test_knowledge_base_routes.py::TestKnowledgeBaseUpload::test_upload_pdf_success
```

### اجرای با coverage

```bash
pytest --cov=api --cov-report=html
```

## تست‌های Cypress

تست‌های E2E با Cypress در پوشه `cypress/` قرار دارند.

### نصب Cypress

```bash
npm install cypress --save-dev
```

### اجرای Cypress

```bash
# GUI mode
npx cypress open

# Headless mode
npx cypress run
```

### پیش‌نیازهای اجرای تست‌های Cypress

1. سرور باید در حال اجرا باشد:
   ```bash
   python -m uvicorn api.app:app --reload
   ```

2. API باید در آدرس `http://localhost:4000` در دسترس باشد

## Fixtures

### Pytest Fixtures (conftest.py)

- `test_db`: Session دیتابیس برای تست‌ها
- `client`: FastAPI TestClient
- `temp_vector_store_dir`: دایرکتوری موقت برای vector stores
- `temp_pdf_uploads_dir`: دایرکتوری موقت برای PDF uploads
- `mock_openai_key`: Mock برای OpenAI API key
- `sample_pdf_content`: محتوای PDF نمونه برای تست
- `sample_pdf_file`: فایل PDF نمونه برای تست

### Cypress Fixtures

- `example.json`: داده‌های نمونه

## نکات مهم

1. تست‌ها از دیتابیس SQLite در حافظه استفاده می‌کنند
2. تست‌ها از Mock برای OpenAI API استفاده می‌کنند تا نیاز به API key واقعی نباشد
3. فایل‌ها و دایرکتوری‌های موقت به صورت خودکار پاک می‌شوند
4. هر تست با یک دیتابیس خالی شروع می‌شود

