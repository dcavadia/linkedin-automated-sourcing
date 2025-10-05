import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

load_dotenv()
EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')

# Chrome options for stealth (less detectable as bot)
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
# options.add_argument("--headless")  # Uncomment for no browser window

# Setup driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    # Login
    driver.get("https://www.linkedin.com/login")
    wait = WebDriverWait(driver, 10)
    
    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    email_field.send_keys(EMAIL)
    
    pw_field = driver.find_element(By.ID, "password")
    pw_field.send_keys(PASSWORD)
    
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_btn.click()
    
    time.sleep(5)  # Delay for load/2FA if needed
    
    # Check if logged in (look for search bar)
    if "www.linkedin.com/feed" in driver.current_url or driver.find_elements(By.CSS_SELECTOR, "[data-tracking-control-name='global-search-input']"):
        print("Login successful! Ready for searches.")
    else:
        print("Login failed—check creds or 2FA.")
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.quit()
