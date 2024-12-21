from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time

# Configuration
AMAZON_LOGIN_URL = "https://www.amazon.in/ap/signin"
BEST_SELLER_URL = "https://www.amazon.in/gp/bestsellers/"
CATEGORIES = [
    "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
    "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
    "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
    "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
    # Add more category URLs here
]
MAX_PRODUCTS = 1500
OUTPUT_FILE = "amazon_best_sellers.json"
USERNAME = "your_amazon_email"
PASSWORD = "your_amazon_password"

# Initialize Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Authenticate to Amazon
def amazon_login():
    driver.get(AMAZON_LOGIN_URL)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        ).send_keys(USERNAME + Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        ).send_keys(PASSWORD + Keys.RETURN)
        print("Login successful!")
    except TimeoutException:
        print("Login failed! Please check your credentials.")
        driver.quit()
        exit()

# Scrape category products
def scrape_category(category_url):
    driver.get(category_url)
    products = []
    try:
        while len(products) < MAX_PRODUCTS:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.zg-grid-general-faceout"))
            )
            items = driver.find_elements(By.CSS_SELECTOR, "div.zg-grid-general-faceout")
            for item in items:
                try:
                    discount_elem = item.find_elements(By.CSS_SELECTOR, "span.promo-badge-text")
                    if discount_elem:
                        discount = discount_elem[0].text
                        discount_value = int(discount.replace("% off", "").strip())
                        if discount_value > 50:
                            product = {
                                "Product Name": item.find_element(By.CSS_SELECTOR, "div.p13n-sc-truncated").text,
                                "Product Price": item.find_element(By.CSS_SELECTOR, "span.p13n-sc-price").text,
                                "Sale Discount": discount,
                                "Best Seller Rating": item.find_element(By.CSS_SELECTOR, "span.a-icon-alt").text,
                                "Ship From": "N/A",
                                "Sold By": "N/A",
                                "Rating": item.find_element(By.CSS_SELECTOR, "a.a-link-normal").get_attribute("title"),
                                "Product Description": "N/A",
                                "Number Bought in the Past Month": "N/A",
                                "Category Name": category_url.split("/")[-1],
                                "All Available Images": [
                                    img.get_attribute("src")
                                    for img in item.find_elements(By.CSS_SELECTOR, "img")
                                ],
                            }
                            products.append(product)
                except NoSuchElementException:
                    continue
            # Pagination
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                if "disabled" in next_button.get_attribute("class"):
                    break
                next_button.click()
                time.sleep(2)
            except NoSuchElementException:
                break
    except TimeoutException as e:
        print(f"Timeout error: {e}")
    return products[:MAX_PRODUCTS]

# Main function
def main():
    amazon_login()
    all_products = []
    for category_url in CATEGORIES:
        print(f"Scraping category: {category_url}")
        category_products = scrape_category(category_url)
        all_products.extend(category_products)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(all_products, file, ensure_ascii=False, indent=4)
    print(f"Scraping completed. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
