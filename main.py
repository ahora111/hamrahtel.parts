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

def categorize_messages(models):
    categories = {"🟥": [], "🟨": [], "🟦": [], "general": []}
    
    for model in models:
        line = model
        if "HUAWEI" in model:
            line = f"🟥 {model}"
            categories["🟥"].append(line)
        elif "REDMI" in model or "POCO" in model:
            line = f"🟨 {model}"
            categories["🟨"].append(line)
        elif "LCD" in model:
            line = f"🟦 {model}"
            categories["🟦"].append(line)
        else:
            categories["general"].append(line)
    
    return categories

def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

def send_telegram_message(message, bot_token, chat_id):
    message = escape_markdown(message)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}
    response = requests.get(url, params=params)
    if response.json().get('ok') is False:
        logging.error(f"❌ خطا در ارسال پیام: {response.json()}")
    else:
        logging.info("✅ پیام ارسال شد!")

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
            categorized_data = categorize_messages(models)
            for category, lines in categorized_data.items():
                if lines:
                    message = "\n".join(lines)  # همه خطوط همان دسته رو به هم وصل می‌کنیم
                    send_telegram_message(message, BOT_TOKEN, CHAT_ID)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")
    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
