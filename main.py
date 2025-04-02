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
import re

# تنظیمات تلگرام
BOT_TOKEN = "8187924543:AAH0jZJvZdpq_34um8R_yCyHQvkorxczXNQ"
CHAT_ID = "-1002683452872"

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ایجاد WebDriver
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


# پیمایش صفحه
def scroll_page(driver, scroll_pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
      
def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

# استخراج داده‌ها
def extract_product_data(driver):
    product_elements = driver.find_elements(By.CLASS_NAME, 'mantine-Text-root')
    models = [product.text.strip() for product in product_elements]
    return models[25:]


# دسته‌بندی داده‌ها با ایموجی‌ها
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





from persiantools.jdatetime import JalaliDate

# ایجاد هدر برای هر دسته‌بندی
def create_header(category):
    today_date = JalaliDate.today().strftime('%Y/%m/%d')
    if category == "LCD":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات سامسونگ ➡️\n\n"
    elif category == "REDMI_POCO":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات شیائومی ➡️\n\n"
    elif category == "HUAWEI":
        return f"📅 بروزرسانی قیمت در تاریخ {today_date} می باشد\n✅ لیست پخش قطعات موبایل اهورا\n⬅️ موجودی قطعات هوآوی ➡️\n\n"
    return ""

# ایجاد فوتر
def create_footer():
    return "\n\n☎️ شماره های تماس :\n📞 09371111558\n📞 02833991417"

# ارسال پیام به تلگرام با هدر و فوتر
def send_categorized_messages(bot_token, chat_id, categorized_data):
    for category, messages in categorized_data.items():
        if messages:
            header = create_header(category)
            footer = create_footer()
            full_message = header + "\n".join(messages) + footer
            response = send_telegram_message(full_message, bot_token, chat_id)
            if response.status_code == 200:
                logging.info(f"✅ پیام برای دسته‌بندی {category} ارسال شد!")
            else:
                logging.error(f"❌ خطا در ارسال پیام برای دسته‌بندی {category}: {response.json()}")

# ارسال پیام به تلگرام
def send_telegram_message(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"}
    response = requests.post(url, params=params)
    return response


# دریافت پیام‌های اخیر تلگرام
def get_last_five_messages(bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)

    if response.status_code == 200:
        updates = response.json().get('result', [])
        messages = [msg for msg in updates if 'message' in msg and str(msg['message']['chat']['id']) == chat_id]
        return messages[-5:]  # دریافت ۵ پیام آخر
    else:
        logging.error("❌ خطا در دریافت پیام‌ها")
        return []


# پیدا کردن پیام دارای ایموجی
def find_message_with_emojis(messages):
    emoji_pattern = re.compile("[\U0001F600-\U0001F64F]|\U0001F300-\U0001F5FF|\U0001F680-\U0001F6FF|\U0001F1E0-\U0001F1FF")
    for message in reversed(messages):  # بررسی از آخرین پیام
        text = message['message'].get('text', '')
        if emoji_pattern.search(text):
            return message['message']['message_id']
    return None


# ارسال پیام همراه با دکمه‌های شیشه‌ای (بهبود یافته)
def send_message_with_buttons(bot_token, chat_id):
    final_message = """
✅ لیست قطعات گوشیای بالا بروز میباشد.
تحویل کالا بعد از ثبت خرید، ساعت 11:30 صبح روز بعد می باشد.

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

    # دریافت پیام‌های اخیر و پیدا کردن پیام با ایموجی
    messages = get_last_five_messages(bot_token, chat_id)
    target_message_id = find_message_with_emojis(messages)

    # ایموجی‌های دسته‌بندی
    emoji_samsung = "🟦"
    emoji_xiaomi = "🟨"
    emoji_huawei = "🟥"

    # ایجاد دکمه شیشه‌ای
    inline_keyboard = {"inline_keyboard": []}  # ایجاد پیش‌فرض برای دکمه‌ها
    if target_message_id:
        inline_keyboard["inline_keyboard"] = [
            [{"text": f"قطعات سامسونگ {emoji_samsung}", "url": f"https://t.me/c/{chat_id.replace('-100', '')}/{target_message_id}"}],
            [{"text": f"قطعات شیایومی {emoji_xiaomi}", "url": f"https://t.me/c/{chat_id.replace('-100', '')}/{target_message_id}"}],
            [{"text": f"قطعات هوآوی {emoji_huawei}", "url": f"https://t.me/c/{chat_id.replace('-100', '')}/{target_message_id}"}]
        ]
    else:
        logging.warning("هیچ پیامی با ایموجی پیدا نشد!")

    # ارسال پیام همراه با دکمه‌ها
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": final_message,
        "reply_markup": json.dumps(inline_keyboard),
    }
    try:
        response = requests.post(url, json=params, timeout=10)
        if response.status_code == 200:
            logging.info("✅ پیام همراه با دکمه شیشه‌ای ارسال شد!")
        else:
            logging.error(f"❌ خطا در ارسال پیام: {response.json()}")
    except requests.exceptions.Timeout:
        logging.error("❌ درخواست ارسال پیام به دلیل تایم‌اوت ناموفق بود!")
    except Exception as e:
        logging.error(f"❌ خطای غیرمنتظره هنگام ارسال پیام: {e}")



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
            send_message_with_buttons(BOT_TOKEN, CHAT_ID)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")
    except Exception as e:
        logging.error(f"❌ خطا: {e}")


if __name__ == "__main__":
    main()
