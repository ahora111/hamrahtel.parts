#!/usr/bin/env python3
import os
import time
import requests
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from persiantools.jdatetime import JalaliDate

# تنظیمات تلگرام
BOT_TOKEN = "8187924543:AAH0jZJvZdpq_34um8R_yCyHQvkorxczXNQ"
CHAT_ID = "-1002683452872"

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_driver():
    """ایجاد WebDriver برای اجرای Selenium"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logging.error(f"خطا در ایجاد WebDriver: {e}")
        return None

def scroll_page(driver, scroll_pause_time=2):
    """اسکرول کردن صفحه برای بارگذاری تمام محصولات"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_parts_data(driver):
    """استخراج داده‌های قطعات موبایل"""
    product_elements = driver.find_elements(By.CLASS_NAME, 'mantine-Text-root')  # بررسی کلاس دقیق
    parts = []

    for product in product_elements:
        text = product.text.strip()
        if text and "تومان" in text:  # فیلتر کردن فقط محصولات دارای قیمت
            parts.append(text.replace("تومان", "").strip())

    return parts[20:]  # حذف آیتم‌های نامربوط احتمالی

def send_telegram_message(message, bot_token, chat_id):
    """ارسال پیام به تلگرام"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2"
    }
    response = requests.post(url, json=params)
    return response.json()

def main():
    try:
        driver = get_driver()
        if not driver:
            logging.error("❌ WebDriver ایجاد نشد!")
            return
        
        driver.get('https://hamrahtel.com/quick-checkout?category=mobile-parts')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'mantine-Text-root')))
        logging.info("✅ داده‌ها آماده‌ی استخراج هستند!")
        scroll_page(driver)

        parts_data = extract_parts_data(driver)
        driver.quit()

        if parts_data:
            update_date = JalaliDate.today().strftime("%Y-%m-%d")
            message = f"📅 *بروزرسانی قیمت قطعات موبایل در تاریخ {update_date}*\n\n" + "\n".join(parts_data) + "\n\n☎️ *شماره تماس:* 📞 09371111558\n📞 02833991417"
            send_telegram_message(message, BOT_TOKEN, CHAT_ID)
            logging.info("✅ پیام ارسال شد!")
        else:
            logging.warning("❌ هیچ داده‌ای برای ارسال پیدا نشد!")

    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
