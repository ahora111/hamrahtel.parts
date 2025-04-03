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
    return models[25:]

def is_number(model_str):
    try:
        float(model_str.replace(",", ""))
        return True
    except ValueError:
        return False

def process_model(model_str):
    model_str = model_str.replace("٬", "").replace(",", "").strip()
    if is_number(model_str):
        model_value = float(model_str)
        model_value_with_increase = model_value * 1.015
        return f"{model_value_with_increase:,.0f}"
    return model_str

def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text



import requests

BOT_TOKEN = "توکن بات خودت را بگذار"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)

print(response.json())




def split_message(message, max_length=4000):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def send_telegram_message(message, bot_token, chat_id):
    message_parts = split_message(message)
    for part in message_parts:
        part = escape_markdown(part)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {"chat_id": chat_id, "text": part, "parse_mode": "MarkdownV2"}
        response = requests.get(url, params=params)
        if response.json().get('ok') is False:
            logging.error(f"❌ خطا در ارسال پیام: {response.json()}")
            return
    logging.info("✅ پیام ارسال شد!")

from persiantools.jdatetime import JalaliDate

from persiantools.jdatetime import JalaliDate

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
            categorized_data[current_key].append(model)
    return categorized_data


# تابعی برای دریافت آخرین ۵ پیام
def get_last_messages(bot_token, chat_id, count=5):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        messages = [update.get("message", {}) for update in data.get("result", []) if "message" in update]
        return messages[-count:]  # دریافت آخرین `count` پیام
    else:
        return []

messages = get_last_messages(BOT_TOKEN, CHAT_ID)
print("📩 پیام‌های دریافت‌شده از تلگرام:")
for msg in messages:
    print(msg)  # نمایش کامل پیام برای تحلیل بهتر


# تابعی برای بررسی پیام و یافتن لینک بر اساس ایموجی
import re

def find_message_with_emoji(messages, emoji):
    for message in messages:
        text = message.get("text", "").strip()
        print(f"🔍 بررسی پیام: {repr(text)}")  # `repr()` برای نمایش کاراکترهای مخفی
        if re.search(re.escape(emoji), text):
            print(f"✅ پیام دارای {emoji} پیدا شد! ID: {message['message_id']}")
            return message['message_id']
    print(f"❌ هیچ پیام دارای {emoji} یافت نشد!")
    return None

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatHistory"
params = {"chat_id": CHAT_ID, "limit": 5}
response = requests.get(url, params=params)
print(response.json())  # خروجی را ارسال کن



    
# تابعی برای ارسال پیام با دکمه‌ها
def send_message_with_buttons(bot_token, chat_id, message, button_links):
    # دکمه‌ها
    buttons = [
        {"text": "قطعات سامسونگ📱", "url": button_links.get('🟦')},
        {"text": "قطعات شیایومی 📱", "url": button_links.get('🟨')},
        {"text": "قطعات هوآوی 📱", "url": button_links.get('🟥')}
    ]
    
    # ساخت ساختار پیام با دکمه‌ها
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "reply_markup": {"inline_keyboard": [[button] for button in buttons]}
    }
    response = requests.get(url, params=params)
    if response.json().get('ok'):
        print("✅ پیام با دکمه‌ها ارسال شد!")
    else:
        print("❌ خطا در ارسال پیام!")
        


def send_final_message(bot_token, chat_id):
    final_message = """
✅ لیست قطعات گوشیای بالا بروز میباشد. تحویل کالا بعد از ثبت خرید، ساعت 11:30 صبح روز بعد می باشد.

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
    send_telegram_message(final_message, bot_token, chat_id)

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
            for category, messages in categorized_data.items():
                if messages:
                    header = create_header(category)
                    footer = create_footer()
                    message = header + "\n".join(messages) + footer
                    send_telegram_message(message, BOT_TOKEN, CHAT_ID)

                # دریافت ۵ پیام آخر
                messages = get_last_messages(BOT_TOKEN, CHAT_ID)
    
                # پیدا کردن پیام‌های مرتبط با هر ایموجی
                button_links = {}
                button_links['🟦'] = find_message_with_emoji(messages, '🟦')
                button_links['🟨'] = find_message_with_emoji(messages, '🟨')
                button_links['🟥'] = find_message_with_emoji(messages, '🟥')
    
                # پیام و دکمه‌ها را ارسال می‌کنیم
                if all(button_links.values()):
                    send_message_with_buttons(BOT_TOKEN, CHAT_ID, "✅ لیست قطعات موبایل بروز شد!", button_links)
                else:
                    print("❌ همه ایموجی‌ها پیدا نشدند!")

            # ارسال پیام پایانی
            send_final_message(BOT_TOKEN, CHAT_ID)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")
    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
