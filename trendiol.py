import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# تابع برای حذف کاراکترهای نامعتبر از نام فایل
def sanitize_filename(filename):
    return "".join(c for c in filename if c not in r'<>:"/\|?*')

def filter_products(products, min_price=None, max_price=None, brand_name=None):
    """
    فیلتر کردن محصولات بر اساس معیارهای کاربر
    """
    filtered_products = []
    for product in products:
        print(f"Processing product: {product}")

        # استخراج قیمت به صورت عدد
        try:
            price_value = int("".join(filter(str.isdigit, product["Price"])))
            print(f"Extracted price: {price_value}")
        except ValueError:
            price_value = None
            print("Failed to extract price, setting price_value to None")

        # اعمال فیلتر قیمت
        if min_price is not None and price_value is not None and price_value < min_price:
            print(f"Product price {price_value} is less than min_price {min_price}, skipping product")
            continue
        if max_price is not None and price_value is not None and price_value > max_price:
            print(f"Product price {price_value} is greater than max_price {max_price}, skipping product")
            continue

        # اعمال فیلتر برند
        if brand_name and brand_name.lower() not in product["Brand"].lower():
            print(f"Product brand {product['Brand']} does not match brand_name {brand_name}, skipping product")
            continue

        print("Product matches filter criteria, adding to filtered list")
        filtered_products.append(product)
    print(f"Filtered products: {filtered_products}")
    return filtered_products

def read_existing_links(group_title):
    """
    خواندن لینک‌های موجود از فایل متنی
    """
    text_filename = f"{group_title}.txt"
    existing_links = set()

    if os.path.exists(text_filename):
        with open(text_filename, "r", encoding="utf-8") as f:
            for line in f:
                existing_links.add(line.strip())

    return existing_links

def save_data_to_files(group_title, data, current_date, existing_links):
    """
    ذخیره اطلاعات در فایل‌های متنی و اکسل، بدون ذخیره تکراری‌ها
    """
    new_data = [product for product in data if product["Link"] not in existing_links]
    if not new_data:
        print("No new products to save.")
        return

    # ذخیره لینک‌ها در فایل متنی
    text_filename = f"{group_title}.txt"
    with open(text_filename, "a", encoding="utf-8") as f:
        for product in new_data:
            f.write(product["Link"] + "\n")

    # ذخیره اطلاعات در فایل اکسل
    excel_filename = f"{group_title}_{current_date}.xlsx"
    if os.path.exists(excel_filename):
        existing_data = pd.read_excel(excel_filename)
        df = pd.concat([existing_data, pd.DataFrame(new_data)], ignore_index=True)
    else:
        df = pd.DataFrame(new_data)
    df.to_excel(excel_filename, index=False)

    print(f"Saved {len(new_data)} new products.")

def save_filtered_data_to_files(group_title, filter_type, filter_value, data, current_date):
    """
    ذخیره داده‌های فیلتر شده در فایل‌های جداگانه برای جستجوهای جدید

    :param group_title: عنوان گروه محصولات
    :param filter_type: نوع فیلتر (مثلاً "price" یا "brand")
    :param filter_value: مقدار فیلتر (مثلاً محدوده قیمت یا نام برند)
    :param data: لیست داده‌های فیلتر شده
    :param current_date: تاریخ فعلی
    """
    filter_description = f"{filter_type}_{filter_value}".replace(" ", "_")
    filename_prefix = f"{group_title}_{filter_description}"

    # ذخیره لینک‌ها در فایل متنی
    text_filename = f"{filename_prefix}.txt"
    with open(text_filename, "w", encoding="utf-8") as f:
        for product in data:
            f.write(product["Link"] + "\n")

    # ذخیره اطلاعات در فایل اکسل
    excel_filename = f"{filename_prefix}_{current_date}.xlsx"
    df = pd.DataFrame(data)
    df.to_excel(excel_filename, index=False)

    print(f"Saved filtered data to {text_filename} and {excel_filename}.")

def scrape_pages_in_batches(driver, base_url, group_title, current_date, min_price=None, max_price=None, brand_name=None, existing_links=set(), max_idle_attempts=10):
    """
    استخراج اطلاعات به صورت گروهی از صفحه با بارگذاری پویا
    با امکان فیلتر محصولات

    :param driver: selenium webdriver instance
    :param base_url: آدرس صفحه اصلی برای اسکرپ
    :param group_title: عنوان گروه محصولات
    :param current_date: تاریخ فعلی
    :param min_price: حداقل قیمت (اختیاری)
    :param max_price: حداکثر قیمت (اختیاری)
    :param brand_name: نام برند (اختیاری)
    :param existing_links: مجموعه لینک‌های موجود
    :param max_idle_attempts: حداکثر تعداد تلاش‌های بدون محصول جدید
    """
    all_links_set = set(existing_links)
    idle_attempts = 0
    total_saved_products = 0
    all_scraped_products = []

    driver.get(base_url)

    # صبر برای بارگذاری اولیه صفحه
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "p-card-wrppr"))
    )

    while idle_attempts < max_idle_attempts:
        product_cards = driver.find_elements(By.CLASS_NAME, "p-card-wrppr")
        print(f"Found {len(product_cards)} product cards.")

        current_products = []
        for idx, card in enumerate(product_cards):
            if idx >= total_saved_products and idx < total_saved_products + 12:
                try:
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                    if link in all_links_set:
                        continue

                    brand = card.find_element(By.CLASS_NAME, "prdct-desc-cntnr-ttl").get_attribute("title")
                    name = card.find_element(By.CLASS_NAME, "prdct-desc-cntnr-name").get_attribute("title")
                    price = card.find_element(By.CLASS_NAME, "prc-box-dscntd").text

                    try:
                        colors = card.find_element(By.CLASS_NAME, "color-variant-count").text
                    except:
                        colors = "ندارد"

                    product = {"Link": link, "Brand": brand, "Name": name, "Price": price, "Colors": colors}
                    current_products.append(product)
                    all_links_set.add(link)
                    all_scraped_products.append(product)

                except Exception as e:
                    print(f"Error processing product card: {e}")

        # ذخیره محصولات جدید
        if current_products:
            save_data_to_files(group_title, current_products, current_date, existing_links)
            total_saved_products += len(current_products)
            idle_attempts = 0  # ریست کردن تعداد تلاش‌های بی‌حاصل
            print(f"Saved {len(current_products)} new products. Total saved: {total_saved_products}")
        else:
            idle_attempts += 1
            print(f"No new products found. Idle attempts: {idle_attempts}")

        # اسکرول به 24مین محصول
        if len(product_cards) >= total_saved_products:
            target_element = product_cards[total_saved_products - 1]
            driver.execute_script("arguments[0].scrollIntoView();", target_element)

        time.sleep(3)  # زمان برای بارگذاری محتوای جدید

        # بررسی تغییرات در تعداد محصولات
        new_product_cards = driver.find_elements(By.CLASS_NAME, "p-card-wrppr")
        if len(new_product_cards) <= len(product_cards):
            idle_attempts += 1
            print(f"No new products loaded. Idle attempts: {idle_attempts}")
        else:
            idle_attempts = 0

    print("Finished scraping. No more new products found.")

    # اعمال فیلتر اگر تعیین شده باشد
    if min_price is not None or max_price is not None or brand_name is not None:
        filtered_products = filter_products(all_scraped_products, min_price, max_price, brand_name)
        
        # ایجاد نام فیلتر برای ذخیره سازی
        filter_description = []
        if min_price is not None:
            filter_description.append(f"min_price_{min_price}")
        if max_price is not None:
            filter_description.append(f"max_price_{max_price}")
        if brand_name is not None:
            filter_description.append(f"brand_{brand_name}")
        
        filter_description_str = "_".join(filter_description)
        save_filtered_data_to_files(group_title, "filtered", filter_description_str, filtered_products, current_date)

    return all_links_set

# تنظیمات مرورگر
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # برای اجرای بدون رابط کاربری (اختیاری)
options.add_argument("--ignore-certificate-errors")  # نادیده گرفتن خطاهای SSL
options.add_argument("--ignore-ssl-errors")  # نادیده گرفتن خطاهای SSL
options.add_argument("--disable-gpu")  # بهینه‌سازی در حالت headless
options.add_argument("--disable-software-rasterizer")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")  # مدیریت حافظه در سرورهای لینوکس
options.add_argument('--allow-insecure-localhost')
options.add_argument('--test-type')
options.add_argument("--disable-web-security")  # نادیده گرفتن خطاهای SSL handshake

# ایجاد درایور
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# دریافت ورودی‌های کاربر
print("لطفاً فیلترهای مورد نظر خود را وارد کنید (اختیاری):")
min_price = input("Minimum Price: ")
max_price = input("Maximum Price: ")
brand_name = input("Brand Name: ")

# تبدیل ورودی‌های عددی به عدد (در صورت خالی بودن مقدار None باقی می‌ماند)
min_price = int(min_price) if min_price.strip().isdigit() else None
max_price = int(max_price) if max_price.strip().isdigit() else None
brand_name = brand_name.strip() if brand_name.strip() else None

# آدرس صفحه اصلی
base_url = "https://www.trendyol.com/erkek-sort-x-g2-c119?pi"

# نام گروه و تاریخ فعلی
group_title = sanitize_filename(base_url.split("/")[-1])
current_date = datetime.now().strftime("%Y-%m-%d")

# خواندن لینک‌های موجود
existing_links = read_existing_links(group_title)

# اسکرپ و فیلتر کردن
scrape_pages_in_batches(
    driver, 
    base_url, 
    group_title, 
    current_date, 
    min_price=min_price, 
    max_price=max_price, 
    brand_name=brand_name, 
    existing_links=existing_links
)

# بستن درایور
driver.quit()
print("اطلاعات با موفقیت استخراج و ذخیره شد.")