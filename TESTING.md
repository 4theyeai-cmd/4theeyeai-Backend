# راهنمای تست‌های خودکار

این پروژه شامل تست‌های خودکار با **Pytest** (برای Backend) و **Cypress** (برای E2E Testing) است.

## 📋 فهرست مطالب

- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [تست‌های Pytest](#تست‌های-pytest)
- [تست‌های Cypress](#تست‌های-cypress)
- [اجرای تست‌ها](#اجرای-تست‌ها)
- [ساختار تست‌ها](#ساختار-تست‌ها)

## نصب و راه‌اندازی

### نصب وابستگی‌های Python

```bash
pip install -r requirements.txt
```

وابستگی‌های تست شامل:
- `pytest>=7.4.0`
- `pytest-cov>=4.1.0`
- `pytest-asyncio>=0.21.0`
- `httpx>=0.25.0`

### نصب Cypress

```bash
npm install
```

یا:

```bash
npm install cypress --save-dev
```

## تست‌های Pytest

### ساختار تست‌ها

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures و تنظیمات
├── test_knowledge_base_routes.py # تست‌های API Routes
├── test_knowledge_base_service.py # تست‌های Unit برای KnowledgeBaseService
├── test_company_document_service.py # تست‌های Unit برای CompanyDocumentService
└── integration/
    └── test_knowledge_base_integration.py # تست‌های Integration
```

### انواع تست‌ها

#### 1. تست‌های Unit

تست‌های unit برای سرویس‌ها:
- `test_knowledge_base_service.py`
- `test_company_document_service.py`

#### 2. تست‌های API Routes

تست‌های endpoint‌های API:
- `test_knowledge_base_routes.py`

#### 3. تست‌های Integration

تست‌های integration برای workflow کامل:
- `tests/integration/test_knowledge_base_integration.py`

### اجرای تست‌های Pytest

```bash
# اجرای تمام تست‌ها
pytest

# اجرای با جزئیات بیشتر
pytest -v

# اجرای تست‌های خاص
pytest tests/test_knowledge_base_routes.py

# اجرای یک تست خاص
pytest tests/test_knowledge_base_routes.py::TestKnowledgeBaseUpload::test_upload_pdf_success

# اجرای فقط تست‌های unit
pytest -m "not integration"

# اجرای فقط تست‌های integration
pytest -m integration

# اجرای با coverage
pytest --cov=api --cov-report=html

# اجرای با coverage و نمایش خطوط
pytest --cov=api --cov-report=term-missing
```

### Fixtures موجود

- `test_db`: Session دیتابیس برای تست‌ها (SQLite در حافظه)
- `client`: FastAPI TestClient
- `temp_vector_store_dir`: دایرکتوری موقت برای vector stores
- `temp_pdf_uploads_dir`: دایرکتوری موقت برای PDF uploads
- `mock_openai_key`: Mock برای OpenAI API key
- `sample_pdf_content`: محتوای PDF نمونه
- `sample_pdf_file`: فایل PDF نمونه

## تست‌های Cypress

### ساختار Cypress

```
cypress/
├── e2e/
│   ├── knowledge-base.cy.js      # تست‌های Knowledge Base API
│   └── api-endpoints.cy.js        # تست‌های عمومی API
├── support/
│   ├── commands.js                # Custom commands
│   └── e2e.js                     # Support file
└── fixtures/
    └── example.json               # Fixture files
```

### اجرای تست‌های Cypress

#### حالت GUI (Interactive)

```bash
npm run test:cypress:open
# یا
npx cypress open
```

#### حالت Headless

```bash
npm run test:cypress
# یا
npx cypress run
```

### پیش‌نیازهای Cypress

1. **سرور باید در حال اجرا باشد:**
   ```bash
   python -m uvicorn api.app:app --reload --port 4000
   ```

2. **API باید در آدرس `http://localhost:4000` در دسترس باشد**

### Custom Commands

Cypress شامل custom commands زیر است:

- `cy.uploadPDF(companyName, filePath, description)`: آپلود PDF
- `cy.waitForAPI(alias)`: انتظار برای پاسخ API
- `cy.checkAPIHealth()`: بررسی سلامت API

## اجرای تست‌ها

### استفاده از اسکریپت‌های کمکی

#### Linux/Mac

```bash
# اجرای تمام تست‌ها
./run_tests.sh all

# فقط Pytest
./run_tests.sh pytest

# فقط Cypress
./run_tests.sh cypress
```

#### Windows

```cmd
REM اجرای تمام تست‌ها
run_tests.bat all

REM فقط Pytest
run_tests.bat pytest

REM فقط Cypress
run_tests.bat cypress
```

### استفاده از npm scripts

```bash
# تست‌های Pytest
npm run test:pytest

# تست‌های Pytest با coverage
npm run test:pytest:cov

# تست‌های Cypress
npm run test:cypress

# تست‌های Cypress (GUI)
npm run test:cypress:open

# تمام تست‌ها
npm run test:all
```

## نکات مهم

### 1. دیتابیس تست

- تست‌های Pytest از SQLite در حافظه استفاده می‌کنند
- هر تست با یک دیتابیس خالی شروع می‌شود
- بعد از هر تست دیتابیس پاک می‌شود

### 2. Mock‌ها

- OpenAI API با Mock جایگزین شده تا نیاز به API key واقعی نباشد
- LangChain embeddings و LLM نیز Mock شده‌اند

### 3. فایل‌های موقت

- تمام فایل‌ها و دایرکتوری‌های موقت به صورت خودکار پاک می‌شوند
- PDF‌ها و vector stores در دایرکتوری‌های موقت ذخیره می‌شوند

### 4. Coverage

برای مشاهده گزارش coverage:

```bash
pytest --cov=api --cov-report=html
```

گزارش HTML در پوشه `htmlcov/index.html` ایجاد می‌شود.

## مثال‌های تست

### تست Unit

```python
def test_upload_pdf_success(client: TestClient, sample_pdf_file):
    """Test successful PDF upload"""
    with open(sample_pdf_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        data = {"company_name": "TestCompany"}
        response = client.post("/api/v1/knowledge-base/upload", files=files, data=data)
    
    assert response.status_code == 200
    assert response.json()["company_name"] == "TestCompany"
```

### تست Integration

```python
def test_full_workflow_upload_and_query(client: TestClient, sample_pdf_file):
    """Test complete workflow: upload PDF and query"""
    # Upload
    # ... upload code ...
    
    # Query
    # ... query code ...
    
    # Verify
    # ... verification code ...
```

### تست Cypress

```javascript
it('should upload a PDF file successfully', () => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('company_name', 'TestCompany');
  
  cy.request({
    method: 'POST',
    url: '/api/v1/knowledge-base/upload',
    body: formData,
  }).then((response) => {
    expect(response.status).to.eq(200);
    expect(response.body.company_name).to.eq('TestCompany');
  });
});
```

## CI/CD

### GitHub Actions مثال

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest --cov=api --cov-report=xml
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: python -m uvicorn api.app:app --port 4000 &
      - run: npx cypress run
```

## پشتیبانی

برای سوالات یا مشکلات:
1. بررسی کنید که تمام وابستگی‌ها نصب شده‌اند
2. مطمئن شوید که سرور در حال اجرا است (برای Cypress)
3. لاگ‌های خطا را بررسی کنید
4. مطمئن شوید که متغیرهای محیطی به درستی تنظیم شده‌اند

## منابع

- [Pytest Documentation](https://docs.pytest.org/)
- [Cypress Documentation](https://docs.cypress.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

