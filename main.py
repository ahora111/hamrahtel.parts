import os
import time
import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from persiantools.jdatetime import JalaliDate

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

import re

def escape_markdown(text):
    """
    این تابع تمام کاراکترهای خاص MarkdownV2 را در متن تلگرام فرار می‌دهد.
    """
    escape_chars = r'_*[\]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)
    
test_text = "قیمت گوشی - سامسونگ: 15.900.000 تومان"
escaped_text = escape_markdown(test_text)
print(escaped_text)




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
    for model in models:
        if "HUAWEI" in model:
            categorized_data["HUAWEI"].append(f"🟥 {model}")
        elif "REDMI" in model or "poco" in model:
            categorized_data["REDMI_POCO"].append(f"🟨 {model}")
        elif "LCD" in model:
            categorized_data["LCD"].append(f"🟦 {model}")
    return categorized_data

def get_last_post_links(bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url).json()

    samsung_link, xiaomi_link, huawei_link = None, None, None

    if "result" in response:
        messages = response["result"]
        for msg in reversed(messages):
            if "message" in msg and "text" in msg["message"]:
                text = msg["message"]["text"]
                msg_id = msg["message"]["message_id"]

                if "🟦" in text and not samsung_link:
                    samsung_link = f"https://t.me/{chat_id}/{msg_id}"
                elif "🟨" in text and not xiaomi_link:
                    xiaomi_link = f"https://t.me/{chat_id}/{msg_id}"
                elif "🟥" in text and not huawei_link:
                    huawei_link = f"https://t.me/{chat_id}/{msg_id}"

                if samsung_link and xiaomi_link and huawei_link:
                    break
    return samsung_link, xiaomi_link, huawei_link

def create_buttons(bot_token, chat_id):
    samsung_link, xiaomi_link, huawei_link = get_last_post_links(bot_token, chat_id)
    buttons = []
    if samsung_link:
        buttons.append(InlineKeyboardButton("قطعات سامسونگ📱", url=samsung_link))
    if xiaomi_link:
        buttons.append(InlineKeyboardButton("قطعات شیایومی 📱", url=xiaomi_link))
    if huawei_link:
        buttons.append(InlineKeyboardButton("قطعات هوآوی📱", url=huawei_link))
    return InlineKeyboardMarkup([buttons])

def send_message_with_buttons(bot_token, chat_id, message):
    keyboard = create_buttons(bot_token, chat_id)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "reply_markup": keyboard.to_json()
    }
    response = requests.get(url, params=params)
    if response.json().get('ok') is False:
        logging.error(f"❌ خطا در ارسال پیام: {response.json()}")
    else:
        logging.info("✅ پیام ارسال شد با دکمه‌ها!")

def main():
    try:
        driver = get_driver()
        if not driver:
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
                    header = f"📅 بروزرسانی قیمت: {JalaliDate.today()}\n✅ لیست پخش قطعات {category}\n"
                    message = header + "\n".join(messages)
                    send_message_with_buttons(BOT_TOKEN, CHAT_ID, message)
            
            final_message = """
✅ لیست قطعات گوشیای بالا بروز میباشد. تحویل کالا بعد از ثبت خرید، ساعت 11:30 صبح روز بعد می باشد.
✅ شماره کارت جهت واریز:
🔷 شماره شبا: IR970560611828006154229701
🔷 شماره کارت: 6219861812467917
🔷 بلو بانک: حسین گرئی
⭕️ رسید واریز به آیدی تلگرام زیر ارسال شود.
🆔 @lhossein1
✅ شماره تماس ثبت سفارش:
📞 09371111558
📞 02833991417
            """
            send_message_with_buttons(BOT_TOKEN, CHAT_ID, final_message)
        else:
            logging.warning("❌ داده‌ای برای ارسال وجود ندارد!")
    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
