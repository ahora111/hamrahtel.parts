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

def split_message(message, max_length=4000):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]
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
    
def send_telegram_message(message, bot_token, chat_id, reply_markup=None):
    message_parts = split_message(message)
    last_message_id = None
    for part in message_parts:
        part = escape_markdown(part)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "MarkdownV2"
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)  # ✅ تبدیل `reply_markup` به JSON

        headers = {"Content-Type": "application/json"}  # ✅ اضافه کردن `headers` برای `POST`
        response = requests.post(url, json=params, headers=headers)  
        response_data = response.json()
        if response_data.get('ok'):
            last_message_id = response_data["result"]["message_id"]
        else:
            logging.error(f"❌ خطا در ارسال پیام: {response_data}")
            return None

    logging.info("✅ پیام ارسال شد!")
    return last_message_id  # برگشت message_id آخرین پیام



def get_last_messages(bot_token, chat_id, limit=5):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    if response.json().get("ok"):
        messages = response.json().get("result", [])
        return [msg for msg in messages if "message" in msg][-limit:]
    return []





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
        
        # استخراج داده‌ها
        brands, models = extract_product_data(driver)
        driver.quit()
        

        samsung_message_id = None  # ذخیره message_id سامسونگ
        xiaomi_message_id = None  # ذخیره message_id شیایومی
        huawei_message_id = None  # ذخیره message_id آیفون
        
        if brands:
            processed_data = []
            for i in range(len(brands)):
                model_str = process_model(models[i])
                processed_data.append(f"{model_str} {brands[i]}")

            update_date = JalaliDate.today().strftime("%Y-%m-%d")
            message_lines = []
            for row in processed_data:
                decorated = decorate_line(row)
                message_lines.append(decorated)

            categories = categorize_messages(message_lines)

            for category, lines in categories.items():
                if lines:
                    header, footer = get_header_footer(category, update_date)
                    message = header + "\n" + "\n".join(lines) + footer
                    msg_id = send_telegram_message(message, BOT_TOKEN, CHAT_ID)

                    if category == "🟦":  # ذخیره message_id سامسونگ
                        samsung_message_id = msg_id
                    elif category == "🟨":  # ذخیره message_id شیایومی
                        xiaomi_message_id = msg_id
                    elif category == "🟥":  # ذخیره message_id هوآوی
                        huawei_message_id = msg_id  # متغیر مناسب را ذخیره کن
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")

        if not samsung_message_id:
            logging.error("❌ پیام سامسونگ ارسال نشد، دکمه اضافه نخواهد شد!")
            return

        # ✅ ارسال پیام نهایی + دکمه‌های لینک به پیام‌های مربوطه
        final_message = (
            "✅ لیست قطعات بالا بروز میباشد. تحویل کالا بعد از ثبت خرید، ساعت 11:30 صبح روز بعد می باشد.\n\n"
            "✅ شماره کارت جهت واریز\n"
            "🔷 شماره شبا : IR970560611828006154229701\n"
            "🔷 شماره کارت : 6219861812467917\n"
            "🔷 بلو بانک   حسین گرئی\n\n"
            "⭕️ حتما رسید واریز به ایدی تلگرام زیر ارسال شود .\n"
            "🆔 @lhossein1\n\n"
            "✅شماره تماس ثبت سفارش :\n"
            "📞 09371111558\n"
            "📞 02833991417"
        )

        button_markup = {"inline_keyboard": []}
        if samsung_message_id:
            button_markup["inline_keyboard"].append([{"text": "📱 لیست قطعات سامسونگ", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{samsung_message_id}"}])
        if xiaomi_message_id:
            button_markup["inline_keyboard"].append([{"text": "📱 لیست قطعات شیایومی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{xiaomi_message_id}"}])
        if huawei_message_id:
            button_markup["inline_keyboard"].append([{"text": "📱 لیست قطعات هوآوی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{huawei_message_id}"}])
    
        send_telegram_message(final_message, BOT_TOKEN, CHAT_ID, reply_markup=button_markup)

    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
