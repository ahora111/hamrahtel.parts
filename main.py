#!/usr/bin/env python3
import os
import time
import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from persiantools.jdatetime import JalaliDate
import json

# تنظیمات تلگرام
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
        # ثبت داده‌های استخراج‌شده برای بررسی
    logging.info(f"📥 داده‌های استخراج‌شده: {models}")
    return models[25:]

def is_number(model_str):
    try:
        float(model_str.replace(",", ""))
        return True
    except ValueError:
        return False

def process_model_with_rounding_and_last_five_digits(model_str):
    model_str = model_str.replace("٬", "").replace(",", "").strip()
    if is_number(model_str):
        model_value = float(model_str)

        if 0 <= model_value < 500_000:
            model_value += 200_000
        elif 500_000 <= model_value < 1_000_000:
            model_value += 220_000
        elif 1_000_000 <= model_value < 2_000_000:
            model_value += 300_000
        elif 2_000_000 <= model_value < 10_000_000:
            model_value = (model_value * 1.10) + 160_000
        elif 10_000_000 <= model_value < 20_000_000:
            model_value = (model_value * 1.08) + 160_000
        elif 20_000_000 <= model_value < 40_000_000:
            model_value = (model_value * 1.07) + 160_000
        elif model_value >= 40_000_000:
            model_value *= 1.05

        # گرد کردن به 4 رقم آخر (نزدیک‌ترین ۱۰٬۰۰۰)
        rounded_value = round(model_value / 10000) * 10000
        return f"{rounded_value:,}".replace(",", "٬")
    
    return model_str



def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

def split_message(message, max_length=4000):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

import time

def send_telegram_message(message, bot_token, chat_id, reply_markup=None, retries=3, delay=5):
    message_parts = split_message(message)
    
    for part in message_parts:
        part = escape_markdown(part)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {"chat_id": chat_id, "text": part, "parse_mode": "MarkdownV2"}
        
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)
        
        for attempt in range(retries):
            try:
                response = requests.post(url, json=params, timeout=10)
                response_data = response.json()
                
                if response_data.get("ok"):
                    logging.info("✅ پیام با موفقیت ارسال شد!")
                    return response_data["result"]["message_id"]
                else:
                    logging.error(f"❌ خطا در ارسال پیام: {response_data}")
            
            except requests.RequestException as e:
                logging.error(f"❌ خطای اتصال در ارسال پیام (تلاش {attempt + 1} از {retries}): {e}")
            
            time.sleep(delay)  # وقفه قبل از تلاش مجدد
        
        logging.error("❌ تمامی تلاش‌ها برای ارسال پیام ناموفق بود!")
        return None


def create_header(category):
    today_date = JalaliDate.today().strftime('%Y/%m/%d')
    if category == "LCD":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات سامسونگ ➡️\n\n"
    elif category == "REDMI_POCO":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات شیایومی ➡️\n\n"
    elif category == "HUAWEI":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات هوآوی ➡️\n\n"
    return ""

def create_footer():
    return "\n\n☎️ شماره های تماس :\n📞 09371111558\n📞 02833991417"

def categorize_data(models):
    categorized_data = {"HUAWEI": [], "REDMI_POCO": [], "LCD": []}
    current_key = None
    for model in models:
        if "HUAWEI" in model:
            current_key = "HUAWEI"
            categorized_data[current_key].append(f"🟥 {model}")
        elif "REDMI" in model or "poco" in model:
            current_key = "REDMI_POCO"
            categorized_data[current_key].append(f"🟨 {model}")
        elif "LCD" in model:
            current_key = "LCD"
            categorized_data[current_key].append(f"🟦 {model}")
        elif current_key:
            # پردازش مدل عددی با گرد کردن پنج رقم آخر
            processed_model = process_model_with_rounding_and_last_five_digits(model)
            categorized_data[current_key].append(processed_model)
    return categorized_data

def create_button_markup(samsung_message_id, xiaomi_message_id, huawei_message_id):
    return {
        "inline_keyboard": [
            [
                {"text": "📱 لیست قطعات سامسونگ", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{samsung_message_id}"}
            ],
            [
                {"text": "📱 لیست قطعات شیایومی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{xiaomi_message_id}"}
            ],
            [
                {"text": "📱 لیست قطعات هوآوی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{huawei_message_id}"}
            ]
        ]
    }

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
            categorized_data = categorize_data(models)
            samsung_message_id = None
            xiaomi_message_id = None
            huawei_message_id = None

            for category, messages in categorized_data.items():
                if messages:
                    header = create_header(category)
                    footer = create_footer()
                    message = header + "\n".join(messages) + footer
                    message_id = send_telegram_message(message, BOT_TOKEN, CHAT_ID)
                    if category == "LCD":
                        samsung_message_id = message_id
                    elif category == "REDMI_POCO":
                        xiaomi_message_id = message_id
                    elif category == "HUAWEI":
                        huawei_message_id = message_id

            if samsung_message_id and xiaomi_message_id and huawei_message_id:
                final_message = """
✅ لیست قطعات گوشیای بالا بروز میباشد. ثبت خرید تا ساعت 10:30 شب انجام میشود و تحویل کالا ساعت 11:30 صبح روز بعد می باشد.

✅ شماره کارت جهت واریز
🔷 شماره شبا : IR970560611828006154229701
🔷 شماره کارت : 6219861812467917
🔷 بلو بانک   حسین گرئی

⭕️ حتما رسید واریز به ایدی تلگرام زیر ارسال شود.
🆔 @lhossein1

✅ شماره تماس ثبت سفارش:
📞 09371111558
📞 02833991417
"""
                button_markup = create_button_markup(samsung_message_id, xiaomi_message_id, huawei_message_id)
                send_telegram_message(final_message, BOT_TOKEN, CHAT_ID, reply_markup=button_markup)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")

    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
