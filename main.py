#!/usr/bin/env python3
import os
import time
import requests
import logging
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from persiantools.jdatetime import JalaliDate

# تنظیمات مربوط به تلگرام
BOT_TOKEN = "8187924543:AAH0jZJvZdpq_34um8R_yCyHQvkorxczXNQ"
CHAT_ID = "-1002683452872"

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_driver():
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
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_product_data(driver):
    product_elements = driver.find_elements(By.CLASS_NAME, 'mantine-Text-root')
    models = [product.text.strip().replace("تومانءء", "") for product in product_elements]
    return models[25:]



# دسته‌بندی پیام‌ها بر اساس کلمات کلیدی
def categorize_messages(models):
    categorized_messages = []  # لیست نهایی برای پیام‌ها
    current_category = ""  # دسته‌بندی فعلی
    current_lines = []  # لیست سطرهای مرتبط با دسته فعلی
    
    for model in models:
        new_category = ""
        if "HUAWEI" in model:
            new_category = "🟥"
        elif "REDMI" in model or "POCO" in model:
            new_category = "🟨"
        elif "LCD" in model:
            new_category = "🟦"
        
        # اگر دسته‌بندی تغییر کرد، پیام قبلی را ذخیره کن
        if new_category:
            if current_lines:
                categorized_messages.append("\n".join(current_lines))
            current_category = new_category
            current_lines = [f"{current_category} {model}"]
        else:
            if current_category:  
                current_lines.append(model)  # اضافه کردن مدل‌های بدون دسته‌بندی به دسته‌ی قبلی
            else:
                categorized_messages.append(model)  # اگر دسته‌بندی نداشت، جداگانه ذخیره شود

    # ذخیره آخرین دسته‌بندی
    if current_lines:
        categorized_messages.append("\n".join(current_lines))
    
    return categorized_messages


def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

import time  # اضافه کردن این خط در ابتدای کد

def send_telegram_message(message, bot_token, chat_id):
    message = escape_markdown(message)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}
    
    response = requests.get(url, params=params)
    
    if response.json().get('ok') is False:
        logging.error(f"❌ خطا در ارسال پیام: {response.json()}")
        if response.json().get('error_code') == 429:  # خطای Too Many Requests
            retry_after = response.json().get('parameters', {}).get('retry_after', 5)
            logging.warning(f"⏳ باید {retry_after} ثانیه صبر کنیم...")
            time.sleep(retry_after)  # صبر قبل از ارسال مجدد
    else:
        logging.info("✅ پیام ارسال شد!")
    
    time.sleep(2)  # وقفه بین ارسال پیام‌ها

def main():
    try:
        driver = get_driver()
        if not driver:
            logging.error("❌ نمی‌توان WebDriver را ایجاد کرد.")
            return
        
        driver.get('https://hamrahtel.com/quick-checkout?category=mobile-parts')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'mantine-Text-root')))
        logging.info("✅ داده‌ها آماده‌ی استخراج هستند!")
        scroll_page(driver)

        models = extract_product_data(driver)
        driver.quit()

        if models:
            # اعمال دسته‌بندی‌ها و افزودن ایموجی‌ها به هر سطر
            decorated_lines = [decorate_line(line) for line in models]
            categorized_messages = categorize_messages(decorated_lines)

            # ارسال پیام‌ها به تلگرام
            for category, lines in categorized_messages.items():
                if lines:
                    message = "\n".join(lines)
                    send_telegram_message(message, BOT_TOKEN, CHAT_ID)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")
    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
