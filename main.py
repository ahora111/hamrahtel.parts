#!/usr/bin/env python3
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

# لیست رنگ‌ها
COLORS = ["مشکی", "آبی", "قرمز", "سبز", "سفید", "سفید صدفی", "طلایی", "نقره‌ای", "خاکستری", "بنفش", "رزگلد", "زرد", "نارنجی"]

# دسته‌بندی‌های نامعتبر
INVALID_CATEGORIES = ["موبایل", "قطعات موبایل", "لپ‌تاپ", "تبلت", "شارژر موبایل", "کیف و قاب", "هدفون و هندزفری", "ساعت و مچ‌بند", "کابل و تبدیل", "جستجو در مدل‌ها"]

def get_driver():
    """ایجاد و مقداردهی WebDriver"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = Service()
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logging.error(f"خطا در ایجاد WebDriver: {e}")
        return None

def scroll_page(driver, pause_time=2):
    """اسکرول کردن صفحه برای بارگذاری همه محصولات"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def is_number(value):
    """بررسی اینکه مقدار، عدد است یا نه"""
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False

def extract_product_data(driver):
    """استخراج اطلاعات محصولات از سایت"""
    product_elements = driver.find_elements(By.CLASS_NAME, 'mantine-Text-root')
    products = []
    last_valid_product = None

    for product in product_elements:
        name = product.text.strip().replace("تومانءء", "").replace("تومان", "").strip()
        if not name or name in INVALID_CATEGORIES:
            continue  

        words = name.split()
        color, price = None, None  

        # تشخیص قیمت
        for i in range(len(words) - 1, -1, -1):
            if is_number(words[i]):
                price = words.pop(i)
                break

        # تشخیص رنگ
        for i in range(len(words) - 1, -1, -1):
            if words[i] in COLORS:
                color = words.pop(i)
                break

        model = " ".join(words)

        if model:
            products.append((model, color, price))
            last_valid_product = (model, color, price)
        elif price and last_valid_product:
            model, color, _ = last_valid_product
            products[-1] = (model, color, price)

    return products

def escape_markdown(text):
    """فرار دادن کاراکترهای خاص برای Markdown"""
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

def split_message(message, max_length=4000):
    """تقسیم پیام طولانی به بخش‌های کوچک‌تر"""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def decorate_line(line):
    """افزودن ایموجی دسته‌بندی به ابتدای هر خط"""
    if "huawei" in line.lower():
        return f"🟥 {line}"
    if any(keyword in line.lower() for keyword in ["poco", "redmi"]):
        return f"🟨 {line}"
    if "lcd" in line.lower():
        return f"🟦 {line}"
    return line

def categorize_messages(lines):
    """دسته‌بندی پیام‌ها بر اساس نوع محصول"""
    categories = {"🟥": [], "🟨": [], "🟦": []}
    for line in lines:
        if line.startswith("🟥"):
            categories["🟥"].append(line)
        elif line.startswith("🟨"):
            categories["🟨"].append(line)
        elif line.startswith("🟦"):
            categories["🟦"].append(line)
    return categories

def get_header_footer(category, update_date):
    """دریافت عنوان و فوتر پیام برای هر دسته‌بندی"""
    headers = {
        "🟥": f"📅 بروزرسانی قیمت در تاریخ {update_date} \n✅ قطعات هوآوی\n",
        "🟨": f"📅 بروزرسانی قیمت در تاریخ {update_date} \n✅ قطعات شیائومی\n",
        "🟦": f"📅 بروزرسانی قیمت در تاریخ {update_date} \n✅ قطعات سامسونگ\n",
    }
    footer = "\n\n☎️ شماره تماس:\n📞 09371111558\n📞 02833991417"
    return headers[category], footer

def send_telegram_message(message, reply_markup=None):
    """ارسال پیام به تلگرام"""
    for part in split_message(escape_markdown(message)):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": part, "parse_mode": "MarkdownV2"}
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)
        response = requests.post(url, json=params)
        response_data = response.json()
        if not response_data.get('ok'):
            logging.error(f"❌ خطا در ارسال پیام: {response_data}")

def main():
    """اجرای اصلی برنامه"""
    try:
        driver = get_driver()
        if not driver:
            return

        driver.get('https://hamrahtel.com/quick-checkout?category=mobile-parts')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'mantine-Text-root')))

        scroll_page(driver)
        products = extract_product_data(driver)
        driver.quit()

        update_date = JalaliDate.today().strftime("%Y-%m-%d")
        message_lines = [decorate_line(f"{model} | {color or '-'} | {price or '-'} تومان") for model, color, price in products]
        categories = categorize_messages(message_lines)
        
        message_ids = {}
        for category, lines in categories.items():
            if lines:
                header, footer = get_header_footer(category, update_date)
                message = header + "\n" + "\n".join(lines) + footer
                message_ids[category] = send_telegram_message(message)

        # ارسال پیام نهایی
        final_message = "✅ لیست قطعات بروز شده است. جهت خرید به پشتیبانی پیام دهید."
        send_telegram_message(final_message)

    except Exception as e:
        logging.error(f"❌ خطای غیرمنتظره: {e}")

if __name__ == "__main__":
    main()
