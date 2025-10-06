import os
import re
from typing import List, Dict, Any, Tuple
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
import requests
import difflib

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import init_db, save_candidates

load_dotenv()
EMAIL = os.getenv('LINKEDIN_EMAIL')
PASSWORD = os.getenv('LINKEDIN_PASSWORD')
_driver = None

def save_debug_html(driver, filename='debug.html'):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"DEBUG: Saved page source to '{filename}'.")

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
        print("Login failed or requires captcha. Please verify credentials or manually solve captcha.")
        _driver.quit()
        _driver = None
        raise
    time.sleep(3)
    return _driver

def get_country_from_location(location: str) -> str | None:
    if not location or location == 'n/a':
        return None
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location)}&format=json&limit=1&addressdetails=1"
        headers = {'User-Agent': 'LinkedInSearchApp/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0].get('address', {}).get('country', '').lower()
        return None
    except Exception as e:
        print(f"DEBUG: Geocoding failed for '{location}': {e} (using fuzzy fallback)")
        return None

def calculate_relevance_score(profile_data: Dict[str, Any], config: Dict[str, Any], full_description: str = '') -> Tuple[float, Dict[str, int]]:
    headline = profile_data.get('headline', '').lower()
    scraped_location = profile_data.get('location', 'n/a').lower()
    scraped_company = profile_data.get('current_company', '').lower()
    est_exp = profile_data.get('experience_years', 3)
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer'])).lower()
    location_filter = config.get('location', '').lower().strip()
    company_filter = config.get('company', '').lower().strip()
    min_exp = config.get('min_exp', 0)
    desc_for_match = full_description.lower() if full_description else headline
    score = 0
    breakdown = {'keywords': 0, 'location': 0, 'company': 0, 'experience': 0}

    keyword_words = base_keywords.split()
    if base_keywords in desc_for_match:
        score += 50
        breakdown['keywords'] = 50
        print(f"DEBUG: Keywords full match in desc: '{base_keywords}'")
    elif any(word in desc_for_match for word in keyword_words):
        score += 25
        breakdown['keywords'] = 25
        print(f"DEBUG: Keywords partial match in desc: some words from '{base_keywords}'")

    loc_pts = 0
    if not location_filter:
        loc_pts = 20
        breakdown['location'] = 20
    else:
        if location_filter in scraped_location:
            loc_pts = 20
            breakdown['location'] = 20
            print(f"DEBUG: Location exact match: '{location_filter}' in '{scraped_location}'")
        else:
            filter_country = get_country_from_location(location_filter)
            scraped_country = get_country_from_location(scraped_location)
            if filter_country and scraped_country and filter_country == scraped_country:
                loc_pts = 15
                breakdown['location'] = 15
                print(f"DEBUG: Location country match: both '{filter_country}'")
            else:
                similarity = difflib.SequenceMatcher(None, location_filter, scraped_location).ratio()
                if similarity > 0.7:
                    loc_pts = 10
                    breakdown['location'] = 10
                    print(f"DEBUG: Location fuzzy match: {similarity:.2f} ({location_filter} ~ {scraped_location})")
                else:
                    loc_pts = 0
                    breakdown['location'] = 0
                    print(f"DEBUG: Location no match: '{location_filter}' vs '{scraped_location}' (sim: {similarity:.2f})")
    score += loc_pts

    comp_pts = 0
    if not company_filter:
        comp_pts = 20
        breakdown['company'] = 20
    else:
        if company_filter in desc_for_match:
            comp_pts = 20
            breakdown['company'] = 20
            print(f"DEBUG: Company full match in desc: '{company_filter}'")
        else:
            fuzzy_company = company_filter.replace(' ', '')
            fuzzy_desc = desc_for_match.replace(' ', '')
            if fuzzy_company in fuzzy_desc:
                comp_pts = 10
                breakdown['company'] = 10
                print(f"DEBUG: Company fuzzy match: '{fuzzy_company}' in desc")
            else:
                comp_pts = 0
                breakdown['company'] = 0
                print(f"DEBUG: Company no match: '{company_filter}' vs desc")
    score += comp_pts

    exp_pts = 0
    full_text = full_description if full_description else (headline + ' ' + scraped_company)
    if min_exp == 0:
        exp_pts = 5
        breakdown['experience'] = 5
    else:
        years_match = re.search(r'(\d+(?:\+\s*)?)\s*(?:years?|yrs?|años?)(?:\s*(?:of\s+)?experience|exp)?', full_text)
        if years_match:
            matched_years = int(years_match.group(1).replace('+', ''))
            est_exp = max(est_exp, matched_years)
        if est_exp >= min_exp:
            exp_pts = 10
            breakdown['experience'] = 10
            print(f"DEBUG: Experience full: {est_exp} >= {min_exp}")
        elif est_exp >= (min_exp * 0.5) or any(word in full_text for word in ['senior', 'lead', 'principal', 'experienced', 'expert']):
            exp_pts = 5
            breakdown['experience'] = 5
            print(f"DEBUG: Experience partial: {est_exp} or keywords in desc")
        else:
            exp_pts = 0
            breakdown['experience'] = 0
            print(f"DEBUG: Experience no match: {est_exp} < {min_exp}")
    score += exp_pts

    total_score = round(score, 1)
    breakdown['total'] = total_score
    print(f"DEBUG: Score calc - Keywords:{breakdown['keywords']}, Loc:{loc_pts}, Comp:{comp_pts}, Exp:{exp_pts} → Total: {total_score}/100")
    return total_score, breakdown

def estimate_experience(headline: str, card_text: str, min_exp: int) -> int:
    full_text = headline + ' ' + card_text
    years_match = re.search(r'(\d+(?:\+\s*)?)\s*(?:years?|años|yr|yrs)', full_text)
    if years_match:
        return int(years_match.group(1).replace('+', ''))
    if any(word in full_text for word in ['senior', 'lead', 'principal']):
        return max(7, min_exp)
    if any(word in full_text for word in ['mid', 'intermediate']):
        return max(4, min_exp // 2)
    if any(word in full_text for word in ['entry', 'junior', 'intern']):
        return 2
    if 'experienced' in full_text or 'expert' in full_text:
        return max(10, min_exp)
    return min_exp if min_exp > 0 else 3

def search_linkedin(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    init_db()
    driver = init_driver()
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer']))
    location = config.get('location', '').strip().lower()
    company = config.get('company', '').strip().lower()
    min_exp = config.get('min_exp', 0)

    query_parts = [f'"{base_keywords}"']
    if location:
        query_parts.append(f'AND "{config["location"]}"')
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
    save_debug_html(driver, 'debug_post_boolean_search.html')

    wait = WebDriverWait(driver, 30)
    cards_loaded = False
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.reusable-search__result-container")))
        print("DEBUG: Initial profile cards loaded.")
        cards_loaded = True
    except TimeoutException:
        print("DEBUG: Timeout on updated cards - trying fallback.")
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list'] li")))
            print("DEBUG: Fallback cards loaded.")
            cards_loaded = True
        except TimeoutException:
            print("DEBUG: No cards loaded - partial page or empty results. Try relaxing terms.")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(5)
    with open('debug_linkedin_search.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("DEBUG: Saved final search HTML.")
    print(f"DEBUG: Final URL: {driver.current_url}")

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    profile_cards = soup.select('ul[role="list"] li')[:3]
    if len(profile_cards) == 0:
        profile_cards = soup.select('li[class*="search-result"], li.reusable-search__result-container, ul.search-results__list li')[:3]
        print(f"DEBUG: Using fallback selector for cards.")
    print(f"DEBUG: Found {len(profile_cards)} profile cards total.")

    for i, card in enumerate(profile_cards):
        card_text = card.get_text()[:200] + "..." if len(card.get_text()) > 200 else card.get_text()
        print(f"DEBUG: Card {i+1} sample text: '{card_text}'")

    profiles = []
    keyword_lower = base_keywords.lower()
    for i, card in enumerate(profile_cards):
        try:
            name_elem = card.select_one('a[href*="/in/"] span[dir="ltr"]')
            full_name = name_elem.get_text(strip=True).strip() if name_elem else f'Candidate {i+1}'
            name = full_name.split('View')[0].strip().split('’s profile')[0].strip()
            link_elem = card.select_one('a[href*="/in/"]')
            profile_url = link_elem['href'] if link_elem else ''

            t14_divs = card.find_all('div', class_=lambda x: x and 't-14' in x and ('t-black' in x or 't-normal' in x))
            headline = ''
            scraped_location = 'N/A'
            if t14_divs:
                for div in t14_divs:
                    classes = div.get('class', [])
                    if classes and 't-black' in ' '.join(classes) and 't-normal' in ' '.join(classes):
                        headline = div.get_text(strip=True).lower()
                        break
                for div in t14_divs:
                    classes = div.get('class', [])
                    if classes and 't-normal' in ' '.join(classes) and 't-black' not in ' '.join(classes):
                        scraped_location_raw = div.get_text(strip=True).lower()
                        scraped_location = scraped_location_raw.title()
                        break

            if not headline:
                card_text_lower = card.get_text().lower()
                headline = card_text_lower.split('·')[0].strip() if '·' in card_text_lower else card_text_lower[:100]
            print(f"DEBUG: Candidate {i+1} ({name}): Headline '{headline[:50]}...'")
            print(f"DEBUG: Candidate {i+1} location: '{scraped_location}'")

            scraped_company = 'N/A'
            if ' at ' in headline:
                scraped_company = headline.split(' at ')[-1].split(' |')[0].split(' ·')[0].strip()
            elif ' | ' in headline:
                scraped_company = headline.split(' | ')[-1].split(' ·')[0].strip()
            elif ' · ' in headline:
                scraped_company = headline.split(' · ')[-1].strip()
            elif '@' in headline:
                scraped_company = headline.split('@')[-1].split()[0].strip()
            scraped_company = scraped_company.lower().replace(',', '')
            print(f"DEBUG: Candidate {i+1} company: '{scraped_company}'")

            card_text = card.get_text()
            full_description = headline + ' ' + card_text

            exp_years = estimate_experience(headline, card_text, min_exp)

            temp_data = {
                'headline': headline,
                'location': scraped_location.lower(),
                'current_company': scraped_company,
                'experience_years': exp_years
            }

            relevance_score, score_breakdown = calculate_relevance_score(temp_data, config, full_description)
            print(f"DEBUG: Candidate {i+1} ({name}) relevance score: {relevance_score}/100")

            linkedin_id_raw = profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else f'candidate_{i+1}'
            linkedin_id = linkedin_id_raw.split('?')[0]

            profiles.append({
                'id': linkedin_id,
                'name': name,
                'skills': [base_keywords],
                'experience_years': exp_years,
                'location': scraped_location,
                'current_company': scraped_company,
                'profile_url': profile_url,
                'relevance_score': relevance_score,
                'score_breakdown': score_breakdown
            })
        except Exception as e:
            print(f"DEBUG: Error processing card {i+1}: {e}")
            if 't14_divs' in locals():
                print(f"DEBUG: Available t-14 divs: {[d.get_text(strip=True)[:50] for d in t14_divs]}")

    print(f"DEBUG: Total candidates added to pool (with scores): {len(profiles)}")

    profiles.sort(key=lambda x: x['relevance_score'], reverse=True)

    saved = save_candidates(profiles)
    print(f"DEBUG: Saved {saved} new candidates to database.")

    driver.quit()
    return profiles
