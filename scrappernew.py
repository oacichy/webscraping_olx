import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random

# Configuration
MAX_PAGES = None  # Set to None to scrape all pages, or specify a number
OUTPUT_FILE = "olx_mieszkania_wlkp2.csv"
BASE_URL = "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/wielkopolskie/"

# Price segmentation settings - STARTING FROM 50,000
MIN_PRICE = 50000   # Starting price (50,000 PLN)
PRICE_STEP = 1000000   # Step between price segments
MAX_PRICE = 3000000  # Maximum price to scrape

# Initialize browser
options = uc.ChromeOptions()
options.headless = True
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 20)

data = []

def accept_cookies():
    try:
        accept_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Akceptuję")]'))
        )
        accept_btn.click()
        print("Cookies accepted.")
    except:
        print("Cookie banner not found or already accepted.")

def extract_size(text):
    """Extract size from text before the '-' character"""
    if ' - ' in text:
        return text.split(' - ')[0].strip()
    return "N/A"

def scrape_page(url):
    driver.get(url)
    time.sleep(random.uniform(2, 4))  # Random delay
    
    # Scroll to load all listings
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(1, 2))
    
    # Wait for listings to load
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-cy="l-card"]')))
    except:
        print("No listings found on this page")
        return False
    
    listings = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="l-card"]')
    
    for listing in listings:
        try:
            # Extract title
            title_element = listing.find_element(By.CSS_SELECTOR, 'div[data-cy="ad-card-title"]')
            title = title_element.text.strip()
            
            # Extract price
            price_element = listing.find_element(By.CSS_SELECTOR, 'p[data-testid="ad-price"]')
            price = price_element.text.strip()
            
            # Extract size (m²)
            try:
                size_element = listing.find_element(By.CSS_SELECTOR, 'span.css-6as4g5')
                size_text = size_element.text.strip()
                size = extract_size(size_text)
            except:
                size = "N/A"

            # Extract location and date
            try:
                location_date_element = listing.find_element(By.CSS_SELECTOR, 'p[data-testid="location-date"]')
                location_date_text = location_date_element.text.strip()
                
                if ' - ' in location_date_text:
                    parts = location_date_text.split(' - ')
                    location = parts[0].strip()
                    date = parts[-1].strip()
                else:
                    location = "N/A"
                    date = location_date_text.strip()
            except:
                location = "N/A"
                date = "N/A"

            data.append({
                'Title': title,
                'Price': price,
                'Size': size,
                'Neighbourhood': location,
                'Date Posted': date,
                'Price Segment': url.split('filter_float_price:from]=')[1].split('&')[0] if 'filter_float_price:from]=' in url else 'N/A'
            })
            
        except Exception as e:
            print(f"Error scraping listing: {str(e)}")
            continue
    
    print(f"Found {len(listings)} listings on this page")
    return True

def get_next_page_url():
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="pagination-forward"]')
        return next_button.get_attribute('href')
    except:
        return None

def scrape_by_price_segments():
    for min_price in range(MIN_PRICE, MAX_PRICE, PRICE_STEP):  # Starts from MIN_PRICE (50,000)
        max_price_segment = min_price + PRICE_STEP
        url = f"{BASE_URL}?search[filter_float_price:from]={min_price}&search[filter_float_price:to]={max_price_segment}"
        print(f"\nScraping price range {min_price}-{max_price_segment} PLN")
        
        # First page
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        accept_cookies()  # Accept cookies on first page
        
        page_num = 1
        while True:
            if MAX_PAGES and page_num > MAX_PAGES:
                print(f"Reached maximum page limit of {MAX_PAGES} for this price segment")
                break
                
            current_url = f"{url}&page={page_num}" if page_num > 1 else url
            print(f"Scraping page {page_num} of price range {min_price}-{max_price_segment} PLN")
            
            success = scrape_page(current_url)
            if not success:
                break
                
            # Check if next page exists
            next_page_url = get_next_page_url()
            if not next_page_url:
                break
                
            page_num += 1
            time.sleep(random.uniform(2, 4))  # Random delay between pages

# Start scraping
try:
    scrape_by_price_segments()
except Exception as e:
    print(f"Error during scraping: {str(e)}")
finally:
    driver.quit()

# Save to CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nSaved {len(data)} listings to {OUTPUT_FILE}")
else:
    print("No data was scraped")