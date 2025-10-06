import os
import re
from typing import List, Dict, Any, Tuple  # Added Tuple
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
import requests  # Added: For Nominatim geocoding (simple API)
import difflib   # Added: Built-in for fuzzy fallback

# Import database functions from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import init_db, save_candidates

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

def get_country_from_location(location: str) -> str | None:
    """Simple Nominatim API to get country from location string (fallback to None)."""
    if not location or location == 'n/a':
        return None
    try:
        # Nominatim search (free, no key; limit=1)
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location)}&format=json&limit=1&addressdetails=1"
        headers = {'User-Agent': 'LinkedInSearchApp/1.0'}  # Required by Nominatim
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
    """Calculate weighted relevance score (0-100) + breakdown. Updated weights: Keywords 50, Loc 20, Comp 20, Exp 10.
    Uses full_description (headline + card_text) for lenient substring matching on keywords/company/exp."""
    headline = profile_data.get('headline', '').lower()
    scraped_location = profile_data.get('location', 'n/a').lower()  # Lower for matching (capitalized version used in output)
    scraped_company = profile_data.get('current_company', '').lower()
    est_exp = profile_data.get('experience_years', 3)
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer'])).lower()
    location_filter = config.get('location', '').lower().strip()
    company_filter = config.get('company', '').lower().strip()
    min_exp = config.get('min_exp', 0)

    # Use full_description if provided (lenient scanning); fallback to headline
    desc_for_match = full_description.lower() if full_description else headline

    score = 0
    breakdown = {'keywords': 0, 'location': 0, 'company': 0, 'experience': 0}  # Track pts for each

    # Keywords (50 pts - high priority; full substring in desc → 50, any word → 25)
    keyword_words = base_keywords.split()
    if base_keywords in desc_for_match:  # Substring containment in full desc
        score += 50  # Full (e.g., "full stack" in "full stack developer...")
        breakdown['keywords'] = 50
        print(f"DEBUG: Keywords full match in desc: '{base_keywords}'")
    elif any(word in desc_for_match for word in keyword_words):  # Any word in desc
        score += 25  # Partial
        breakdown['keywords'] = 25
        print(f"DEBUG: Keywords partial match in desc: some words from '{base_keywords}'")
    keyword_pts = breakdown['keywords']

    # Location (20 pts - unchanged: exact/geocode/fuzzy on scraped_location.lower())
    loc_pts = 0
    if not location_filter:
        loc_pts = 20  # No filter, full credit
        breakdown['location'] = 20
    else:
        # Exact substring
        if location_filter in scraped_location:
            loc_pts = 20
            breakdown['location'] = 20
            print(f"DEBUG: Location exact match: '{location_filter}' in '{scraped_location}'")
        else:
            # Geocode both to check same country (hierarchical; e.g., Caracas -> Venezuela)
            filter_country = get_country_from_location(location_filter)
            scraped_country = get_country_from_location(scraped_location)
            if filter_country and scraped_country and filter_country == scraped_country:
                loc_pts = 15  # Same country (city/country match)
                breakdown['location'] = 15
                print(f"DEBUG: Location country match: both '{filter_country}'")
            elif filter_country == scraped_country:  # If one fails, check other
                loc_pts = 15
                breakdown['location'] = 15
            else:
                # Fallback: Fuzzy similarity (difflib; >70% → partial)
                similarity = difflib.SequenceMatcher(None, location_filter, scraped_location).ratio()
                if similarity > 0.7:
                    loc_pts = 10  # Loose partial (e.g., spelling variations)
                    breakdown['location'] = 10
                    print(f"DEBUG: Location fuzzy match: {similarity:.2f} ({location_filter} ~ {scraped_location})")
                else:
                    loc_pts = 0
                    breakdown['location'] = 0
                    print(f"DEBUG: Location no match: '{location_filter}' vs '{scraped_location}' (sim: {similarity:.2f})")
    score += loc_pts

    # Company (20 pts - medium priority; substring in desc → 20, fuzzy → 10)
    comp_pts = 0
    if not company_filter:
        comp_pts = 20  # No filter, full
        breakdown['company'] = 20
    else:
        if company_filter in desc_for_match:  # Substring in full desc (lenient)
            comp_pts = 20  # Full
            breakdown['company'] = 20
            print(f"DEBUG: Company full match in desc: '{company_filter}'")
        else:
            # Fuzzy: space-removed version
            fuzzy_company = company_filter.replace(' ', '')  # e.g., "google inc" -> "googleinc"
            fuzzy_desc = desc_for_match.replace(' ', '')  # Apply to desc too
            if fuzzy_company in fuzzy_desc:
                comp_pts = 10  # Partial
                breakdown['company'] = 10
                print(f"DEBUG: Company fuzzy match: '{fuzzy_company}' in desc")
            else:
                comp_pts = 0
                breakdown['company'] = 0
                print(f"DEBUG: Company no match: '{company_filter}' vs desc")
    score += comp_pts

    # Experience (10 pts - low priority; enhanced regex/keywords in full desc)
    exp_pts = 0
    full_text = full_description if full_description else (headline + ' ' + scraped_company)  # Use provided or fallback
    if min_exp == 0:
        exp_pts = 5  # Baseline if no filter
        breakdown['experience'] = 5
    else:
        # Enhanced regex: Catches "5 years", "5+ years", "over 5 years", "5 yrs exp", etc.
        years_match = re.search(r'(\d+(?:\+\s*)?)\s*(?:years?|yrs?|años?)(?:\s*(?:of\s+)?experience|exp)?', full_text)
        if years_match:
            matched_years = int(years_match.group(1).replace('+', ''))  # Handle "5+" as 5
            est_exp = max(est_exp, matched_years)  # Update est if better match
        if est_exp >= min_exp:
            exp_pts = 10  # Full
            breakdown['experience'] = 10
            print(f"DEBUG: Experience full: {est_exp} >= {min_exp}")
        elif est_exp >= (min_exp * 0.5) or any(word in full_text for word in ['senior', 'lead', 'principal', 'experienced', 'expert']):
            exp_pts = 5  # Partial (half or keywords)
            breakdown['experience'] = 5
            print(f"DEBUG: Experience partial: {est_exp} or keywords in desc")
        else:
            exp_pts = 0
            breakdown['experience'] = 0
            print(f"DEBUG: Experience no match: {est_exp} < {min_exp}")
    score += exp_pts

    total_score = round(score, 1)
    breakdown['total'] = total_score  # Include total in breakdown
    print(f"DEBUG: Score calc - Keywords:{keyword_pts}, Loc:{loc_pts}, Comp:{comp_pts}, Exp:{exp_pts} → Total: {total_score}/100")
    return total_score, breakdown  # Return breakdown for API

def estimate_experience(headline: str, card_text: str, min_exp: int) -> int:
    """Estimate years from headline/card text (enhanced for reliability; called before scoring)."""
    full_text = headline + ' ' + card_text
    # Regex for years (improved, but scoring uses even better version)
    years_match = re.search(r'(\d+(?:\+\s*)?)\s*(?:years?|años|yr|yrs)', full_text)
    if years_match:
        return int(years_match.group(1).replace('+', ''))
    # Keyword fallbacks (expanded)
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
    # Init DB on search start
    init_db()
    
    driver = init_driver()
    base_keywords = ' '.join(config.get('keywords', ['AI Engineer']))
    location = config.get('location', '').strip().lower()
    company = config.get('company', '').strip().lower()
    min_exp = config.get('min_exp', 0)

    # Build boolean query (unchanged)
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
            # Name: Robust - a with /in/ href, span dir=ltr (cleaned)
            name_elem = card.select_one('a[href*="/in/"] span[dir="ltr"]')
            full_name = name_elem.get_text(strip=True).strip() if name_elem else f'Candidate {i+1}'
            name = full_name.split('View')[0].strip().split('’s profile')[0].strip()  # Clean artifacts
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
                        scraped_location_raw = div.get_text(strip=True).lower()  # Lower for matching
                        scraped_location = scraped_location_raw.title()  # New: Capitalize for display (e.g., "venezuela" → "Venezuela")
                        break

            # Fallback if no t14_divs: Use full card text snippets
            if not headline:
                card_text_lower = card.get_text().lower()
                headline = card_text_lower.split('·')[0].strip() if '·' in card_text_lower else card_text_lower[:100]

            print(f"DEBUG: Candidate {i+1} ({name}): Headline '{headline[:50]}...'")

            print(f"DEBUG: Candidate {i+1} location: '{scraped_location}'")  # Now capitalized

            # Current company: Parse from headline (e.g., after "at " or "|") - for scoring only (but now desc uses full card_text)
            scraped_company = 'N/A'
            if ' at ' in headline:
                scraped_company = headline.split(' at ')[-1].split(' |')[0].split(' ·')[0].strip()
            elif ' | ' in headline:
                scraped_company = headline.split(' | ')[-1].split(' ·')[0].strip()
            elif ' · ' in headline:
                scraped_company = headline.split(' · ')[-1].strip()
            elif '@' in headline:  # Enhanced for "@ company"
                scraped_company = headline.split('@')[-1].split()[0].strip()
            scraped_company = scraped_company.lower().replace(',', '')  # Clean
            print(f"DEBUG: Candidate {i+1} company: '{scraped_company}'")

            # Full card text for lenient matching
            card_text = card.get_text()
            full_description = headline + ' ' + card_text  # For keywords/company/exp scanning

            # Exp: Initial estimation (scoring refines it)
            exp_years = estimate_experience(headline, card_text, min_exp)

            # Temp profile data for scoring (use lowercased location for matching)
            temp_data = {
                'headline': headline,
                'location': scraped_location.lower(),  # Lower for scoring/geocoding
                'current_company': scraped_company,
                'experience_years': exp_years
            }

            # Calculate score (now pass full_description for lenient checks)
            relevance_score, score_breakdown = calculate_relevance_score(temp_data, config, full_description)

            print(f"DEBUG: Candidate {i+1} ({name}) relevance score: {relevance_score}/100")

            # Clean linkedin_id: username only (split '?' for params)
            linkedin_id_raw = profile_url.split('/in/')[-1].split('/')[0] if '/in/' in profile_url else f'candidate_{i+1}'
            linkedin_id = linkedin_id_raw.split('?')[0]  # Remove "?miniProfileUrn..."

            # Always add to pool with score (full for now; subset saved) + breakdown (new, for API only)
            profiles.append({
                'id': linkedin_id,  # Now clean linkedin_id
                'name': name,
                'skills': [base_keywords],
                'experience_years': exp_years,  # Internal only
                'location': scraped_location,  # New: Capitalized for display
                'current_company': scraped_company,  # Internal only
                'profile_url': profile_url,
                'relevance_score': relevance_score,
                'score_breakdown': score_breakdown  # For frontend summary (not saved to DB)
            })

        except Exception as e:
            print(f"DEBUG: Error processing card {i+1}: {e}")
            if t14_divs:
                print(f"DEBUG: Available t-14 divs: {[d.get_text(strip=True)[:50] for d in t14_divs]}")

    print(f"DEBUG: Total candidates added to pool (with scores): {len(profiles)}")
    # Sort by score descending for frontend
    profiles.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Save to DB (subset only) – no breakdown in DB, but location capitalized there too
    saved = save_candidates(profiles)
    print(f"DEBUG: Saved {saved} new candidates to database.")
    
    driver.quit()
    return profiles

# search_node: Example integration (uncomment/adapt for LangGraph/FastAPI)
# def search_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     config = state.get('config', {})  # From input
#     profiles = search_linkedin(config)
#     return {'candidates': profiles, 'search_complete': True}
