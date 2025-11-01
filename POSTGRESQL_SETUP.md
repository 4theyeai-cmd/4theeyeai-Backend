# PostgreSQL Setup Guide for Airport AI Bot

## مراحل راه‌اندازی PostgreSQL

### 1. **نصب وابستگی‌ها**
```bash
pip install -r requirements.txt
```

### 2. **ایجاد فایل .env**
در ریشه پروژه فایل `.env` ایجاد کنید:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Sheets Configuration
KNOWLEDGE_SHEET_ID=your_google_sheet_id_here

# External Extract Info Service
EXTERNAL_EXTRACTINFO_SERVICE_URL=your_external_service_url_here

# PostgreSQL Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password_here
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=airport_bot

# Environment
ENVIRONMENT=development
```

### 3. **ایجاد دیتابیس PostgreSQL**
در PostgreSQL سرور خود:

```sql
CREATE DATABASE airport_bot;
```

### 4. **تست اتصال دیتابیس**
```bash
python test_postgres_connection.py
```

### 5. **راه‌اندازی کامل دیتابیس**
```bash
python setup_postgres.py
```

این اسکریپت:
- متغیرهای محیطی را بررسی می‌کند
- اتصال دیتابیس را تست می‌کند
- مایگریشن‌های Alembic را اجرا می‌کند

### 6. **اجرای دستی مایگریشن‌ها (اختیاری)**
```bash
# ایجاد مایگریشن جدید
alembic revision --autogenerate -m "Initial migration"

# اجرای مایگریشن‌ها
alembic upgrade head

# بررسی وضعیت مایگریشن‌ها
alembic current
alembic history
```

### 7. **اجرای سرور**
```bash
python -m uvicorn api.app:app --reload
```

## تغییرات انجام شده

### ✅ **فایل‌های به‌روزرسانی شده:**

1. **`api/database/database.py`** - تنظیمات PostgreSQL
2. **`api/app.py`** - اضافه کردن POSTGRES_PASSWORD به متغیرهای اجباری
3. **`alembic/env.py`** - تنظیم Alembic برای استفاده از متغیرهای محیطی
4. **`alembic.ini`** - تنظیم URL دیتابیس
5. **`api/services/extract_info_service.py`** - بهبود مدیریت خطا

### ✅ **فایل‌های جدید:**

1. **`test_postgres_connection.py`** - تست اتصال PostgreSQL
2. **`setup_postgres.py`** - اسکریپت راه‌اندازی کامل
3. **`POSTGRESQL_SETUP.md`** - راهنمای کامل

## عیب‌یابی

### مشکل: "OPENAI_API_KEY is not set"
**راه حل:** فایل `.env` را ایجاد کنید و `OPENAI_API_KEY` را تنظیم کنید.

### مشکل: "POSTGRES_PASSWORD environment variable is not set"
**راه حل:** در فایل `.env` رمز عبور PostgreSQL را تنظیم کنید.

### مشکل: "Connection refused"
**راه حل:** 
- سرور PostgreSQL را بررسی کنید
- آدرس و پورت را در فایل `.env` بررسی کنید
- فایروال را بررسی کنید

### مشکل: "Database does not exist"
**راه حل:** دیتابیس `airport_bot` را در PostgreSQL ایجاد کنید.

## مزایای PostgreSQL

✅ **عملکرد بهتر** - برای حجم داده‌های بالا  
✅ **امنیت بیشتر** - سیستم احراز هویت قوی  
✅ **پشتیبانی از JSON** - برای داده‌های پیچیده  
✅ **مقیاس‌پذیری** - برای رشد آینده  
✅ **پشتیبانی از تراکنش‌ها** - برای داده‌های حساس  

## نکات مهم

- **رمز عبور قوی** استفاده کنید
- **فایل .env** را در `.gitignore` قرار دهید
- **پشتیبان‌گیری** منظم از دیتابیس انجام دهید
- **مانیتورینگ** اتصالات دیتابیس را فعال کنید
