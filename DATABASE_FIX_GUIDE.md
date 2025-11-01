# Database Table Fix Guide

## مشکل: UndefinedColumn error

خطای `column "airportName" of relation "trips" does not exist` نشان می‌دهد که جدول `trips` در دیتابیس PostgreSQL وجود دارد اما ستون‌های آن درست ایجاد نشده‌اند.

## دلایل احتمالی:

1. **جدول قدیمی** - جدول از قبل وجود دارد اما ستون‌های جدید ندارد
2. **مایگریشن ناقص** - مایگریشن‌ها درست اجرا نشده‌اند
3. **تغییر مدل‌ها** - مدل‌ها تغییر کرده‌اند اما دیتابیس به‌روزرسانی نشده

## راه‌حل‌های موجود:

### 🛠️ **راه‌حل 1: اصلاح فقط جدول trips (توصیه شده)**

```bash
python fix_trips_table.py
```

این اسکریپت:
- ✅ فقط جدول `trips` و `passengers` را اصلاح می‌کند
- ✅ سایر جداول را دست نمی‌زند
- ✅ داده‌های موجود را حفظ می‌کند
- ✅ ساختار جدول را بررسی می‌کند

### 🛠️ **راه‌حل 2: اصلاح تمام جداول (کامل)**

```bash
python fix_database_tables.py
```

این اسکریپت:
- ⚠️ تمام جداول را حذف و دوباره ایجاد می‌کند
- ⚠️ تمام داده‌های موجود را از دست می‌دهید
- ✅ تمام مشکلات دیتابیس را حل می‌کند

### 🛠️ **راه‌حل 3: استفاده از Alembic (پیشرفته)**

```bash
# ایجاد مایگریشن جدید
alembic revision --autogenerate -m "Fix trips table structure"

# اجرای مایگریشن
alembic upgrade head
```

## مراحل توصیه شده:

### 1. **بررسی وضعیت فعلی**
```bash
python check_database.py
```

### 2. **اصلاح جدول trips**
```bash
python fix_trips_table.py
```

### 3. **تست endpoint**
```bash
python test_trips_endpoint.py
```

### 4. **تست کامل سیستم**
```bash
python test_all_endpoints.py
```

## ساختار صحیح جدول trips:

```sql
CREATE TABLE trips (
    id VARCHAR PRIMARY KEY,
    "airportName" VARCHAR NOT NULL,
    "travelDate" VARCHAR NOT NULL,
    "flightNumber" VARCHAR NOT NULL
);

CREATE TABLE passengers (
    id VARCHAR PRIMARY KEY,
    trip_id VARCHAR NOT NULL,
    "fullName" VARCHAR NOT NULL,
    "nationalId" VARCHAR NOT NULL,
    "luggageCount" INTEGER NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);
```

## نکات مهم:

### ⚠️ **قبل از اجرا:**
- از داده‌های مهم پشتیبان تهیه کنید
- مطمئن شوید که سرور متوقف است
- فایل `.env` را بررسی کنید

### ✅ **بعد از اجرا:**
- سرور را مجدداً راه‌اندازی کنید
- endpoint ها را تست کنید
- لاگ‌ها را بررسی کنید

### 🔧 **عیب‌یابی:**

**مشکل: "Permission denied"**
```bash
# بررسی دسترسی‌های دیتابیس
psql -h your_host -U your_user -d your_db -c "\dt"
```

**مشکل: "Connection refused"**
```bash
# بررسی اتصال دیتابیس
python test_postgres_connection.py
```

**مشکل: "Table still has wrong structure"**
```bash
# بررسی ساختار جدول
psql -h your_host -U your_user -d your_db -c "\d trips"
```

## مثال خروجی موفق:

```
🚀 Trips Table Fix
==================================================
🔍 Checking trips table structure...
❌ Missing columns: ['airportName', 'travelDate', 'flightNumber']
⚠️  This will recreate the trips table. Continue? (y/N): y
🔧 Fixing trips table...
🗑️  Dropping trips table...
🔧 Creating trips table...
🔧 Creating passengers table...
✅ Tables created successfully!
✅ All required columns exist
🧪 Testing trips operations...
✅ Test data inserted successfully
📋 Retrieved data:
  - Trip: test-123 | Airport: Test Airport | Date: 2024-01-01 | Flight: TEST123
    Passenger: Test Passenger | ID: 1234567890 | Luggage: 2
🧹 Test data cleaned up
🎉 Trips table fixed successfully!
```

## پیشگیری از مشکلات آینده:

1. **همیشه از Alembic استفاده کنید** برای تغییرات دیتابیس
2. **تست‌های واحد بنویسید** برای مدل‌های دیتابیس
3. **مستندات به‌روز نگه دارید** برای تغییرات schema
4. **پشتیبان‌گیری منظم** انجام دهید
