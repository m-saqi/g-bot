import os
import time
import logging
from flask import Flask, request, jsonify, render_template

# Import the modern, maintained library
from cfl_selenium import SChromeDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Professional Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchBot:

    def setup_driver(self):
        """
        This function now uses the cfl_selenium library (chrome-for-lambda-selenium),
        which is the modern standard for running Selenium on Vercel.
        """
        try:
            # SChromeDriver from the new library handles all setup automatically.
            driver = SChromeDriver()
            logger.info("SChromeDriver setup successful using cfl_selenium.")
            return driver
        except Exception as e:
            logger.error(f"FATAL: Driver setup failed. Error: {str(e)}")
            raise

    def find_and_click_link(self, driver, target_domain):
        """
        Finds and clicks the target link using a robust selector.
        """
        try:
            # This selector finds the clickable h3 title of a search result.
            links = driver.find_elements(By.CSS_SELECTOR, "a > h3")
            
            for i, link in enumerate(links[:10]):
                parent_a_tag = link.find_element(By.XPATH, "..")
                href = parent_a_tag.get_attribute('href')
                
                if href and target_domain in href:
                    logger.info(f"Target '{target_domain}' found at position {i + 1}: {href}")
                    parent_a_tag.click()
                    return href, i + 1
                    
            logger.warning(f"Target domain '{target_domain}' not found in search results.")
            return None, None
        except Exception as e:
            logger.error(f"Error while finding and clicking link: {str(e)}")
            return None, None

    def execute_search_flow(self, query, target_domain):
        """
        The main, streamlined execution flow for the bot.
        """
        driver = None
        start_time = time.time()
        result = {'success': False, 'error': 'An unknown error occurred.', 'steps': []}

        try:
            # Step 1: Initialize Driver
            result['steps'].append({'step': 'Driver Initialization', 'status': 'In Progress'})
            driver = self.setup_driver()
            result['steps'][-1]['status'] = 'Completed'

            # Step 2: Perform Google Search
            result['steps'].append({'step': 'Google Search', 'status': 'In Progress'})
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "search")))
            result['steps'][-1]['status'] = 'Completed'

            # Step 3: Find and Click Target Link
            result['steps'].append({'step': 'Finding Target Link', 'status': 'In Progress'})
            target_url, position = self.find_and_click_link(driver, target_domain)
            if not target_url:
                raise Exception(f"Could not find a link for '{target_domain}' on the search results page.")
            result['steps'][-1]['status'] = 'Completed'

            # Step 4: Confirm Navigation
            result['steps'].append({'step': 'Confirming Navigation', 'status': 'In Progress'})
            WebDriverWait(driver, 15).until(lambda d: "google.com" not in d.current_url)
            logger.info(f"Successfully navigated to: {driver.current_url}")
            result['steps'][-1]['status'] = 'Completed'
            
            # --- Success ---
            result['success'] = True
            result['error'] = None
            result['final_url'] = driver.current_url
            result['page_title'] = driver.title
            logger.info("Search flow completed successfully.")

        except Exception as e:
            error_message = f"Error during '{result['steps'][-1]['step']}': {str(e)}"
            logger.error(error_message)
            result['error'] = error_message
            if result['steps']:
                result['steps'][-1]['status'] = 'Failed'
                
        finally:
            if driver:
                driver.quit()
            result['total_duration'] = round(time.time() - start_time, 2)
        
        return result

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

        if not query or not website:
            return jsonify({'success': False, 'error': 'Query and Website are required.'}), 400
        
        website_domain = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        result = search_bot.execute_search_flow(query, website_domain)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.critical(f"A critical error occurred in the API endpoint: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal Server Error. Check the Vercel logs for details.'}), 500
