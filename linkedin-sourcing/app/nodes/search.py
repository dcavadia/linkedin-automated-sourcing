import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
from app.state import Candidate

load_dotenv()
EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')

_driver = None

def init_driver():
    global _driver
    if _driver:
        return _driver

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    _driver = webdriver.Chrome(service=service, options=options)
    _driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    _driver.get("https://www.linkedin.com/login")

    wait = WebDriverWait(_driver, 15)
    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    email_field.clear()
    email_field.send_keys(EMAIL)

    pw_field = _driver.find_element(By.ID, "password")
    pw_field.clear()
    pw_field.send_keys(PASSWORD)

    login_btn = _driver.find_element(By.XPATH, "//button[@type='submit']")
    login_btn.click()

    try:
        WebDriverWait(_driver, 15).until(
            EC.presence_of_element_located((By.ID, "global-nav-search"))
        )
    except TimeoutException:
        print("Login failed or requires captcha. Please verify credentials or manually solve captcha and try again.")
        _driver.quit()
        _driver = None
        raise

    time.sleep(3)
    return _driver

def apply_location_filter(driver, location_name: str):
    wait = WebDriverWait(driver, 25)

    all_dropdowns = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='button'][data-view-name='search-filter-top-bar-select']")))

    location_dropdown = None
    for dropdown in all_dropdowns:
        try:
            label = dropdown.find_element(By.TAG_NAME, 'label')
            if label.text.strip() == 'Ubicaciones':
                location_dropdown = dropdown
                break
        except Exception as e:
            print(f"Dropdown label read error: {e}")

    if not location_dropdown:
        print("Could not find 'Ubicaciones' dropdown")
        return False

    print("Clicking 'Ubicaciones' dropdown")
    location_dropdown.click()
    time.sleep(1)

    location_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='typeahead-input' and @data-view-name='search-filter-top-bar-menu-tyah']")))
    print(f"Located location input: classes={location_input.get_attribute('class')[:50]} placeholder={location_input.get_attribute('placeholder')}")

    location_input.clear()
    time.sleep(0.5)

    for char in location_name:
        location_input.send_keys(char)
        time.sleep(0.15)
    print(f"Typed '{location_name}' into location input with send_keys")

    dropdown_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='typeahead-results-container']")))

    dropdown_options = []
    start_time = time.time()
    while time.time() - start_time < 12:
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")
        if dropdown_options:
            break
        time.sleep(0.5)
        print(f"Waiting for dropdown options... found {len(dropdown_options)}")

    if not dropdown_options:
        print(f"No dropdown options for {location_name}")
        return False

    first_option = dropdown_options[0]
    print("Clicking first option")

    try:
        first_option.click()
    except StaleElementReferenceException:
        print("Stale reference; refinding first option")
        refreshed_options = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")
        if refreshed_options:
            refreshed_options[0].click()
        else:
            print("Could not refind option to click")
            return False

    apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Mostrar resultados')]")))
    print("Clicking 'Mostrar resultados' button")
    apply_button.click()

    time.sleep(4)
    return True

def apply_current_company_filter(driver, company_name: str):
    wait = WebDriverWait(driver, 25)

    all_dropdowns = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div[role='button'][data-view-name='search-filter-top-bar-select']")
        )
    )

    company_dropdown = None
    for dropdown in all_dropdowns:
        try:
            label = dropdown.find_element(By.TAG_NAME, 'label')
            if label.text.strip() == 'Empresas actuales':
                company_dropdown = dropdown
                break
        except Exception as e:
            print(f"Dropdown label read error: {e}")

    if not company_dropdown:
        print("Could not find 'Empresas actuales' dropdown")
        return False

    print("Clicking 'Empresas actuales' dropdown")
    company_dropdown.click()
    time.sleep(1)

    company_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='typeahead-input' and @data-view-name='search-filter-top-bar-menu-tyah']")))
    print(f"Located company input: classes={company_input.get_attribute('class')[:50]} placeholder={company_input.get_attribute('placeholder')}")

    company_input.clear()
    time.sleep(0.5)


    for char in company_name:
        company_input.send_keys(char)
        time.sleep(0.15)
    print(f"Typed '{company_name}' into company input with send_keys")

    dropdown_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='typeahead-results-container']")))

    dropdown_options = []
    start_time = time.time()
    while time.time() - start_time < 12:
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")
        if dropdown_options:
            break
        time.sleep(0.5)
        print(f"Waiting for dropdown options... found {len(dropdown_options)}")

    if not dropdown_options:
        print(f"No dropdown options for {company_name}")
        return False

    first_option = dropdown_options[0]
    print("Clicking first option")
    try:
        first_option.click()
    except Exception:
        print("Click failed, refinding and retrying")
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, "div[role='option']")
        if dropdown_options:
            dropdown_options[0].click()
        else:
            print("Could not refind option")
            return False

    apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Mostrar resultados')]")))
    print("Clicking 'Mostrar resultados' button")
    apply_button.click()
    time.sleep(4)
    return True

def matches_location_filter(scraped_location: str, filter_location: str) -> bool:
    if filter_location == '' or filter_location == 'any':
        return True
    if filter_location == 'remote':
        return 'remote' in scraped_location.lower() or 'home' in scraped_location.lower()
    scraped_lower = scraped_location.lower()
    filter_lower = filter_location.lower()
    filter_words = filter_lower.split()
    for word in filter_words:
        if word and word in scraped_lower:
            return True
    return False

def search_linkedin(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    driver = init_driver()
    keywords = ' '.join(config.get('keywords', ['AI Engineer']))
    location = config.get('location', 'Venezuela')
    company = config.get('company', None)
    min_exp = config.get('min_exp', 0)

    base_url = "https://www.linkedin.com/search/results/people/"
    params = f"?keywords={keywords.replace(' ', '%20')}&origin=SWITCH_SEARCH_VERTICAL"
    search_url = base_url + params

    driver.get(search_url)

    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-view-name=people-search-result]")))
    except TimeoutException:
        print("Timeout waiting for initial profile cards.")
        return []

    filter_success = apply_location_filter(driver, location)
    if not filter_success:
        print("Location filter failed—proceeding without it.")

    if company:
        filter_success_company = apply_current_company_filter(driver, company)
        if not filter_success_company:
            print("Company filter failed—proceeding without it.")

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-view-name=people-search-result]")))
    except TimeoutException:
        print("Timeout waiting for profile cards after applying filters.")
        return []

    with open('debug_linkedin_search.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("Saved LinkedIn search page HTML as 'debug_linkedin_search.html'.")

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    profile_cards = soup.select('div[data-view-name=people-search-result]')[:3]
    print(f"Found {len(profile_cards)} profile cards using selector 'div[data-view-name=people-search-result]'.")

    profiles = []
    for i, card in enumerate(profile_cards):
        try:
            link_elem = card.select_one('a[data-view-name=search-result-lockup-title]')
            if link_elem:
                name = link_elem.get_text(strip=True)
                profile_url = link_elem['href']
                profile_id = profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else 'unknown'
            else:
                name = 'Unknown'
                profile_id = 'unknown'
                profile_url = ''

            title_elem = card.select_one('p[class*=search-result-lockup-subline], div[class*=subtitle]')
            raw_title = title_elem.get_text(strip=True) if title_elem else ''
            title = 'N/A'
            if raw_title:
                if ' en ' in raw_title:
                    title = raw_title.split(' en ')[0].strip()
                elif any(word in raw_title.lower() for word in keywords.lower().split() + ['engineer', 'developer']):
                    title = raw_title

            location_elem = card.select_one('span[class*=search-result-lockup-region], div[class*=location]')
            location_text = location_elem.get_text(strip=True) if location_elem else 'N/A'

            exp_years = max(min_exp, 3)

            location_match = matches_location_filter(location_text, location)
            exp_match = exp_years >= min_exp

            print(f"DEBUG: Card {i+1} - {name}, {title}, {location_text}, exp {exp_years}, location_match: {location_match}")

            if exp_match and location_match:
                print(f"DEBUG: Adding profile: {name}")
                current_company = raw_title.split(' en ')[-1] if ' en ' in raw_title else title

                profiles.append({
                    'id': profile_id,
                    'name': name,
                    'skills': [keywords],
                    'experience_years': exp_years,
                    'location': location_text,
                    'current_company': current_company,
                    'profile_url': profile_url
                })
            else:
                print(f"DEBUG: Skipping profile: {name} (exp: {exp_match}, loc: {location_match})")
        except Exception as e:
            print(f"Parse error on card {i+1}: {e}")
            continue

    driver.quit()
    print(f"Extracted {len(profiles)} matching profiles.")
    return profiles

def search_node(state) -> 'AppState':
    profiles = search_linkedin(state.config)
    for profile in profiles:
        state.candidates.append(Candidate(
            linkedin_id=profile['id'],
            name=profile['name'],
            profile_data=profile,
            status='pending'
        ))
    state.metrics['total_searched'] = len(profiles)
    return state
