import os
import time
import random
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchBot:
    def __init__(self):
        self.ua = UserAgent()

    def setup_driver(self):
        """
        Sets up a headless Chrome driver optimized for a serverless environment.
        """
        try:
            chrome_options = Options()
            # Essential options for running in a containerized/serverless environment
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            
            # Anti-bot detection measures
            chrome_options.add_argument(f'user-agent={self.ua.random}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Use webdriver-manager to automatically handle the ChromeDriver
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Further stealth measure
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Driver setup successful.")
            return driver
        except Exception as e:
            logger.error(f"Driver setup failed: {str(e)}")
            raise

    def find_and_click_link(self, driver, target_domain):
        """
        Scans search results for a link containing the target domain and clicks it.
        This uses a more robust selector that targets the main clickable title of a search result.
        """
        try:
            # This selector is more stable as it targets the main 'h3' title within a link
            links = driver.find_elements(By.CSS_SELECTOR, "a > h3")
            
            for i, link in enumerate(links[:10]):  # Check top 10 results
                parent_a_tag = link.find_element(By.XPATH, "..")
                href = parent_a_tag.get_attribute('href')
                
                if href and target_domain in href:
                    logger.info(f"Target '{target_domain}' found at position {i + 1}: {href}")
                    # Use JavaScript click for better reliability in headless mode
                    driver.execute_script("arguments[0].click();", parent_a_tag)
                    return href, i + 1
                    
            logger.warning(f"Target domain '{target_domain}' not found in the first 10 results.")
            return None, None
        except Exception as e:
            logger.error(f"Error while finding and clicking link: {str(e)}")
            return None, None

    def execute_search_flow(self, query, target_domain, scroll_duration):
        """
        Main execution flow for the bot.
        """
        driver = None
        start_time = time.time()
        session_data = {'success': False, 'error': None, 'steps': [], 'metrics': {}}

        try:
            # 1. Initialize Driver
            session_data['steps'].append({'step': 'Driver Initialization', 'status': 'In Progress'})
            driver = self.setup_driver()
            session_data['steps'][-1]['status'] = 'Completed'

            # 2. Perform Google Search
            session_data['steps'].append({'step': 'Google Search', 'status': 'In Progress'})
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "search")))
            session_data['steps'][-1]['status'] = 'Completed'

            # 3. Find and Click Target
            session_data['steps'].append({'step': 'Link Discovery', 'status': 'In Progress'})
            target_url, position = self.find_and_click_link(driver, target_domain)
            if not target_url:
                raise Exception(f"Could not find '{target_domain}' in search results.")
            session_data['steps'][-1]['status'] = 'Completed'
            session_data['metrics']['search_position'] = position

            # 4. Wait for Page Load and Simulate Visit
            session_data['steps'].append({'step': 'Website Visit', 'status': 'In Progress'})
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info(f"Successfully navigated to target. Simulating a visit for {scroll_duration} seconds.")
            time.sleep(scroll_duration) # Simple wait to simulate a user staying on the page
            session_data['steps'][-1]['status'] = 'Completed'
            
            # Success
            session_data['success'] = True
            session_data['final_url'] = driver.current_url
            session_data['metrics']['total_duration'] = round(time.time() - start_time, 2)
            logger.info("Search flow completed successfully.")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Search flow failed: {error_msg}")
            session_data['error'] = error_msg
            # Mark the current step as failed
            if session_data['steps']:
                session_data['steps'][-1]['status'] = 'Failed'
                
        finally:
            if driver:
                driver.quit()
        
        return session_data

# --- Flask Application ---
app = Flask(__name__)
search_bot = SearchBot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        website = data.get('website', '').strip()
        scroll_duration = min(max(int(data.get('scroll_duration', 8)), 3), 30)

        if not query or not website:
            return jsonify({'success': False, 'error': 'Query and Website are required.'}), 400
        
        website_domain = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        logger.info(f"API Request: Search for '{query}' and visit '{website_domain}'")
        result = search_bot.execute_search_flow(query, website_domain, scroll_duration)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
