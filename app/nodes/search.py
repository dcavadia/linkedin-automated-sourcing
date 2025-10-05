import os
import re
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

def calculate_relevance_score(profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
    """Calculate weighted relevance score (0-100) based on 4 filters with priorities."""
    headline = profile_data.get('headline', '').lower()
    scraped_location = profile_data.get('location', '').lower()
    scraped_company = profile_data.get('current_company', '').lower()
    est_exp = profile_data.get('experience_years', 3)
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer'])).lower()
    location_filter = config.get('location', '').lower()
    company_filter = config.get('company', '').lower()
    min_exp = config.get('min_exp', 0)

    score = 0

    # Keywords (35 pts - high priority)
    keyword_words = base_keywords.split()
    if base_keywords in headline:
        score += 35  # Exact
    elif any(word in headline for word in keyword_words):
        score += 20  # Partial
    keyword_pts = score

    # Location (35 pts - high priority)
    loc_pts = 0
    if location_filter:
        if location_filter in scraped_location:
            loc_pts = 35  # Exact
        else:
            # Fuzzy: Check for key cities/regions (customizable dict)
            fuzzy_map = {
                'venezuela': ['caracas', 'maracaibo', 'south america', 'latam', 'colombia', 'bogota'],
                'germany': ['berlin', 'munich', 'europe'],
                # Add more as needed
            }
            fuzzy_terms = fuzzy_map.get(location_filter, [])
            if any(term in scraped_location for term in fuzzy_terms):
                loc_pts = 20  # Partial/fuzzy
        score += loc_pts
    else:
        loc_pts = 35  # No filter, full credit

    # Company (20 pts - medium priority)
    comp_pts = 0
    if company_filter:
        if company_filter in scraped_company:
            comp_pts = 20  # Exact
        else:
            # Simple fuzzy: variants like "corp", "inc"
            fuzzy_company = company_filter.replace(' ', '')  # e.g., "nvidia corp" -> "nvidiacorp"
            if fuzzy_company in scraped_company.replace(' ', ''):
                comp_pts = 10  # Partial
        score += comp_pts
    else:
        comp_pts = 20  # No filter, full

    # Experience (10 pts - low priority)
    exp_pts = 0
    if min_exp == 0:
        exp_pts = 5  # Baseline if no filter
    elif est_exp >= min_exp:
        exp_pts = 10  # Full
    elif est_exp >= (min_exp * 0.5) or 'senior' in headline or 'lead' in headline:
        exp_pts = 5  # Partial
    score += exp_pts

    total_score = round(score, 1)
    print(f"DEBUG: Score calc - Keywords:{keyword_pts}, Loc:{loc_pts}, Comp:{comp_pts}, Exp:{exp_pts} → Total: {total_score}/100")
    return total_score

def estimate_experience(headline: str, card_text: str, min_exp: int) -> int:
    """Estimate years from headline/card text (enhanced for reliability)."""
    full_text = headline + ' ' + card_text
    # Regex for years (improved)
    years_match = re.search(r'(\d+)\s*(?:years?|años|yr|yrs)', full_text)
    if years_match:
        return int(years_match.group(1))
    # Fuzzy words (expanded)
    if any(word in full_text for word in ['senior', 'lead', 'principal']):
        return max(7, min_exp)  # Assume 7+ for senior roles
    if any(word in full_text for word in ['mid', 'intermediate']):
        return max(4, min_exp // 2)
    if any(word in full_text for word in ['entry', 'junior', 'intern']):
        return 2
    if 'experienced' in full_text or 'expert' in full_text:
        return max(10, min_exp)
    return min_exp if min_exp > 0 else 3  # Default

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

    profiles = []  # All candidates added, with scores
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

            # Exp: Enhanced estimation
            card_text = card.get_text()
            exp_years = estimate_experience(headline, card_text, min_exp)

            # Temp profile data for scoring
            temp_data = {
                'headline': headline,
                'location': scraped_location,
                'current_company': scraped_company,
                'experience_years': exp_years
            }

            # Calculate score
            relevance_score = calculate_relevance_score(temp_data, config)

            print(f"DEBUG: Candidate {i+1} ({name}) relevance score: {relevance_score}/100")

            # Always add to pool with score
            profiles.append({
                'id': profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else f'candidate_{i+1}',
                'name': name,
                'skills': [base_keywords],
                'experience_years': exp_years,
                'location': scraped_location,
                'current_company': scraped_company,
                'profile_url': profile_url,
                'relevance_score': relevance_score
            })

        except Exception as e:
            print(f"DEBUG: Error processing card {i+1}: {e}")
            if t14_divs:
                print(f"DEBUG: Available t-14 divs: {[d.get_text(strip=True)[:50] for d in t14_divs]}")

    print(f"DEBUG: Total candidates added to pool (with scores): {len(profiles)}")
    # Sort by score descending for frontend
    profiles.sort(key=lambda x: x['relevance_score'], reverse=True)
    driver.quit()
    return profiles

# search_node omitted - add if needed
