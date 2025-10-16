# استفاده از نسخه سبک پایتون
FROM python:3.11-slim

# تنظیم مسیر کاری
WORKDIR /app

# کپی فایل نیازمندی‌ها و نصب آن‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی بقیه فایل‌های پروژه
COPY backend/src /app

# باز کردن پورت پیش‌فرض Django
EXPOSE 8000

# اجرای سرور جنگو
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
