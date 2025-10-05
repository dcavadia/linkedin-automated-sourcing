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
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
# from app.state import Candidate  # Commented: Not used

load_dotenv()
EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')

_driver = None

def save_debug_html(driver, filename='debug.html'):
    """Save page source for inspection at key points."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"DEBUG: Saved page source to '{filename}' (open in browser to inspect elements).")

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

def search_linkedin(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    driver = init_driver()
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer']))
    location = config.get('location', '').strip().lower()
    company = config.get('company', '').strip().lower()
    min_exp = config.get('min_exp', 0)

    # Build boolean query (same as before)
    query_parts = [f'"{base_keywords}"']  # Exact phrase
    if location:
        query_parts.append(f'AND "{config["location"]}"')  # Use original case for query
    if company:
        query_parts.append(f'AND "{config["company"]}"')
    if min_exp > 0:
        exp_phrase = f'("{min_exp} years experience" OR "{min_exp}+ years")'
        query_parts.append(f'AND {exp_phrase}')
    full_query = ' '.join(query_parts)
    print(f"DEBUG: Built boolean query: '{full_query}' (base: '{base_keywords}', loc: '{location}', company: '{company}', min_exp: {min_exp})")

    base_url = "https://www.linkedin.com/search/results/people/"
    params = f"?keywords={full_query.replace(' ', '%20')}&origin=SWITCH_SEARCH_VERTICAL"
    search_url = base_url + params
    print(f"DEBUG: Navigating to boolean search URL: {search_url}")

    driver.get(search_url)
    print(f"DEBUG: Search page loaded - URL: {driver.current_url}, Title: {driver.title}")

    save_debug_html(driver, 'debug_post_boolean_search.html')  # For inspection

    wait = WebDriverWait(driver, 30)
    cards_loaded = False
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.reusable-search__result-container")))
        print("DEBUG: Initial profile cards loaded (updated selector).")
        cards_loaded = True
    except TimeoutException:
        print("DEBUG: Timeout on updated cards - trying fallback.")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list'] li")))
            print("DEBUG: Fallback cards loaded (ul[role='list'] li).")
            cards_loaded = True
        except TimeoutException:
            print("DEBUG: No cards loaded - partial page or empty results from boolean query. Try relaxing terms (e.g., remove quotes/exp).")

    # Scroll to load more if needed
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(5)

    with open('debug_linkedin_search.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("DEBUG: Saved final search HTML as 'debug_linkedin_search.html'.")
    print(f"DEBUG: Final URL: {driver.current_url}")

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Robust card selector: ul[role="list"] li (matches HTML structure)
    profile_cards = soup.select('ul[role="list"] li')[:3]
    # Fallback if 0
    if len(profile_cards) == 0:
        profile_cards = soup.select('li[class*="search-result"], li.reusable-search__result-container, ul.search-results__list li')[:3]
        print(f"DEBUG: Using fallback selector for cards.")
    print(f"DEBUG: Found {len(profile_cards)} profile cards total.")

    # Print sample card text if any
    for i, card in enumerate(profile_cards):
        card_text = card.get_text()[:200] + "..." if len(card.get_text()) > 200 else card.get_text()
        print(f"DEBUG: Card {i+1} sample text: '{card_text}'")

    profiles = []  # Only add if all matches
    exp_years = min_exp if min_exp > 0 else 3  # Default/fuzzy for cards
    keyword_lower = base_keywords.lower()
    t14_divs = None  # For headline/location

    for i, card in enumerate(profile_cards):
        try:
            # Name: Robust - a with /in/ href, span dir=ltr
            name_elem = card.select_one('a[href*="/in/"] span[dir="ltr"]')
            name = name_elem.get_text(strip=True).strip() if name_elem else f'Candidate {i+1}'
            link_elem = card.select_one('a[href*="/in/"]')
            profile_url = link_elem['href'] if link_elem else ''

            # All t-14 divs in card for parsing headline/location
            t14_divs = card.find_all('div', class_=lambda x: x and 't-14' in x and ('t-black' in x or 't-normal' in x))
            headline = ''
            scraped_location = 'N/A'
            if t14_divs:
                # First bold (t-black) is headline
                for div in t14_divs:
                    classes = div.get('class', [])
                    if classes and 't-black' in ' '.join(classes) and 't-normal' in ' '.join(classes):
                        headline = div.get_text(strip=True).lower()
                        break
                # Next non-bold (t-normal without t-black) is location
                for div in t14_divs:
                    classes = div.get('class', [])
                    if classes and 't-normal' in ' '.join(classes) and 't-black' not in ' '.join(classes):
                        scraped_location = div.get_text(strip=True).lower()
                        break

            # Fallback if no t14_divs: Use full card text snippets
            if not headline:
                card_text_lower = card.get_text().lower()
                headline = card_text_lower.split('·')[0].strip() if '·' in card_text_lower else card_text_lower[:100]

            print(f"DEBUG: Candidate {i+1} ({name}): Headline '{headline[:50]}...'")

            print(f"DEBUG: Candidate {i+1} location: '{scraped_location}'")

            # Current company: Parse from headline (e.g., after "at " or "|")
            scraped_company = 'N/A'
            if ' at ' in headline:
                scraped_company = headline.split(' at ')[-1].split(' |')[0].split(' ·')[0].strip()
            elif ' | ' in headline:
                scraped_company = headline.split(' | ')[-1].split(' ·')[0].strip()
            elif ' · ' in headline:
                scraped_company = headline.split(' · ')[-1].strip()
            scraped_company = scraped_company.lower().replace(',', '')  # Clean
            print(f"DEBUG: Candidate {i+1} company: '{scraped_company}'")

            # Exp: Fuzzy - if "senior" or min_exp in headline, bump; else default
            if min_exp > 0 and any(word in headline for word in ['senior', 'lead', f'{min_exp}+', f'{min_exp} years']):
                exp_years = max(exp_years, min_exp + 1)

            # Matches
            keyword_match = keyword_lower in headline
            location_match = location in scraped_location if location else True
            company_match = company in scraped_company if company else True
            exp_match = exp_years >= min_exp

            print(f"DEBUG: Candidate {i+1} ({name}) matches - keywords: {keyword_match} (in '{headline}'), location: {location_match} ('{location}' in '{scraped_location}'), company: {company_match} ('{company}' in '{scraped_company}'), exp: {exp_match} ({exp_years} >= {min_exp})")

            if keyword_match and location_match and company_match and exp_match:
                print(f"DEBUG: All matches - adding {name} to pool.")
                profiles.append({
                    'id': profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else f'candidate_{i+1}',
                    'name': name,
                    'skills': [base_keywords],
                    'experience_years': exp_years,
                    'location': scraped_location,
                    'current_company': scraped_company,
                })
            else:
                print(f"DEBUG: Candidate {i+1} failed verification - skipped.")

        except Exception as e:
            print(f"DEBUG: Error processing card {i+1}: {e}")
            if t14_divs:
                print(f"DEBUG: Available t-14 divs: {[d.get_text(strip=True)[:50] for d in t14_divs]}")

    print(f"DEBUG: Total matching profiles added to pool: {len(profiles)}")
    return profiles
