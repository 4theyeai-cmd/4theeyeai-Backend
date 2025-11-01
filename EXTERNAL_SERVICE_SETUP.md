# External Extract Info Service Setup

## تغییرات انجام شده

### ✅ **سرویس extract_info به‌روزرسانی شد:**

1. **حذف فراخوانی مستقیم OpenAI** - دیگر مستقیماً OpenAI را فراخوانی نمی‌کند
2. **استفاده از سرویس خارجی** - از `EXTERNAL_EXTRACTINFO_SERVICE_URL` استفاده می‌کند
3. **حفظ سازگاری** - تابع `call_openai` همچنان کار می‌کند (backward compatibility)
4. **اعتبارسنجی خروجی** - خروجی سرویس خارجی را اعتبارسنجی می‌کند

## فرمت درخواست به سرویس خارجی

```json
{
  "messages": [
    {
      "id": "1755320084411",
      "text": "سلام می‌خوام به نیویورک سفر کنم",
      "sender": "CLIENT"
    },
    {
      "id": "1755320102152", 
      "text": "فرودگاه امام خمینی",
      "sender": "CLIENT"
    }
  ]
}
```

## فرمت خروجی مورد انتظار از سرویس خارجی

```json
{
  "airportName": "فرودگاه امام خمینی",
  "travelDate": "۲۸ مرداد ۱۴۰۴",
  "flightNumber": "",
  "passengers": [
    {
      "fullName": "نام مسافر",
      "nationalId": "کد ملی",
      "luggageCount": 2
    }
  ]
}
```

## متغیرهای محیطی جدید

### فایل `.env`:
```env
# External Extract Info Service
EXTERNAL_EXTRACTINFO_SERVICE_URL=https://your-external-service.com/extract-info
```

## تست سرویس خارجی

```bash
python test_external_service.py
```

این اسکریپت:
- سرویس خارجی را تست می‌کند
- فرمت درخواست و پاسخ را بررسی می‌کند
- خطاها را گزارش می‌دهد

## مزایای استفاده از سرویس خارجی

✅ **جداسازی مسئولیت‌ها** - منطق استخراج اطلاعات جدا شده  
✅ **مقیاس‌پذیری** - سرویس خارجی می‌تواند جداگانه مقیاس شود  
✅ **انعطاف‌پذیری** - امکان تغییر سرویس بدون تغییر کد اصلی  
✅ **امنیت** - کلیدهای API در سرویس خارجی محافظت می‌شوند  
✅ **مانیتورینگ** - امکان مانیتورینگ جداگانه سرویس خارجی  

## نکات مهم

### برای سرویس خارجی:
- **Timeout**: 30 ثانیه
- **Content-Type**: application/json
- **Method**: POST
- **Response**: باید JSON باشد

### برای سرویس اصلی:
- **Backward Compatibility**: تابع `call_openai` همچنان کار می‌کند
- **Error Handling**: خطاهای سرویس خارجی مدیریت می‌شوند
- **Validation**: خروجی سرویس خارجی اعتبارسنجی می‌شود

## عیب‌یابی

### مشکل: "EXTERNAL_EXTRACTINFO_SERVICE_URL is not set"
**راه حل:** متغیر محیطی را در فایل `.env` تنظیم کنید.

### مشکل: "External service error: 404"
**راه حل:** URL سرویس خارجی را بررسی کنید.

### مشکل: "External service error: 500"
**راه حل:** سرویس خارجی را بررسی کنید.

### مشکل: "Missing field in response"
**راه حل:** سرویس خارجی باید تمام فیلدهای مورد انتظار را برگرداند.

## مثال کامل

### درخواست:
```json
{
  "messages": [
    {"id": "1", "text": "می‌خوام به تهران سفر کنم", "sender": "CLIENT"},
    {"id": "2", "text": "تاریخ سفر؟", "sender": "AVATAR"},
    {"id": "3", "text": "۱۵ فروردین", "sender": "CLIENT"}
  ]
}
```

### پاسخ:
```json
{
  "airportName": "تهران",
  "travelDate": "۱۵ فروردین",
  "flightNumber": "",
  "passengers": []
}
```
