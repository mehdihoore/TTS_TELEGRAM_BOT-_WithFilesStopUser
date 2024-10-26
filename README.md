# تلگرام بات تبدیل متن به گفتار
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

این بات تلگرام متون فارسی را به گفتار با صدای طبیعی تبدیل می‌کند. این بات از Microsoft Edge TTS برای تولید صدای با کیفیت بالا استفاده می‌کند.

## امکانات
- پشتیبانی از فرمت‌های TXT، PDF و DOCX
- استفاده از دو صدای فارسی مختلف (فرید و دلارا)
- تبدیل خودکار پاراگراف‌ها به فایل صوتی
- اضافه کردن مکث بین پاراگراف‌ها
- بررسی و رفع خودکار مشکلات فایل‌های MP3
- مدیریت همزمان چندین درخواست کاربر

## پیش‌نیازها
```
python 3.8+
telethon
edge-tts
pydub
python-docx
PyMuPDF
psutil
ffmpeg
```

## نصب
1. ابتدا مخزن را کلون کنید:
```bash
git clone https://github.com/YOUR-USERNAME/telegram-tts-bot.git
cd telegram-tts-bot
```

2. پیش‌نیازها را نصب کنید:
```bash
pip install -r requirements.txt
```

3. ffmpeg را نصب کنید:
- برای اوبونتو:
```bash
sudo apt-get install ffmpeg
```
- برای مک:
```bash
brew install ffmpeg
```
- برای ویندوز از [سایت رسمی ffmpeg](https://ffmpeg.org/download.html) دانلود کنید

4. فایل تنظیمات را ویرایش کنید:
- نام فایل `config.py` را از `config.py.example` کپی کنید
- اطلاعات API تلگرام خود را در آن وارد کنید:
```python
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"
```

## راه‌اندازی
```bash
python bot.py
```

## نحوه استفاده
1. بات را در تلگرام استارت کنید
2. یک فایل متنی (TXT, PDF, یا DOCX) به بات ارسال کنید
3. بات به صورت خودکار فایل را پردازش کرده و یک فایل صوتی برای شما ارسال می‌کند

## ساختار پروژه
```
telegram-tts-bot/
│
├── bot.py            # فایل اصلی بات
├── config.py         # تنظیمات بات
├── requirements.txt  # پیش‌نیازهای پروژه
└── README.md         # مستندات
```

