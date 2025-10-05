import os
import time
import random
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchBot:
    def __init__(self):
        self.ua = UserAgent()
        self.setup_complete = False
        
    def setup_driver(self):
     """Setup Chrome driver with professional configuration"""
     try:
         chrome_options = Options()
         
         # Basic options
         chrome_options.add_argument('--no-sandbox')
         chrome_options.add_argument('--disable-dev-shm-usage')
         chrome_options.add_argument('--disable-gpu')
         chrome_options.add_argument('--disable-blink-features=AutomationControlled')
         
         # Stealth options
         chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
         chrome_options.add_experimental_option('useAutomationExtension', False)
         
         # Performance options
         chrome_options.add_argument('--disable-extensions')
         chrome_options.add_argument('--disable-plugins')
         chrome_options.add_argument('--disable-background-timer-throttling')
         chrome_options.add_argument('--disable-backgrounding-occluded-windows')
         chrome_options.add_argument('--disable-renderer-backgrounding')
         
         # Always run headless on production
         chrome_options.add_argument('--headless=new')
         
         # Random viewport
         width = random.randint(1200, 1920)
         height = random.randint(800, 1080)
         chrome_options.add_argument(f'--window-size={width},{height}')
         
         # Random user agent
         user_agent = self.ua.random
         chrome_options.add_argument(f'--user-agent={user_agent}')
         
         # Use webdriver-manager to handle the driver
         driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
         
         # Additional stealth
         driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
         driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
         
         self.setup_complete = True
         return driver
         
     except Exception as e:
         logger.error(f"Driver setup failed: {str(e)}")
         raise

    def human_delay(self, min_seconds=1, max_seconds=4):
        """Realistic human delay with random variation"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def simulate_reading_behavior(self, driver, element=None):
        """Simulate reading behavior with random eye movements"""
        try:
            if element:
                actions = ActionChains(driver)
                # Move to element with slight offset
                actions.move_to_element_with_offset(element, random.randint(-50, 50), random.randint(-50, 50))
                actions.perform()
            
            # Random micro-delays for reading
            time.sleep(random.uniform(0.5, 2.0))
            
        except Exception:
            pass

    def advanced_scrolling(self, driver, duration=10):
        """Advanced human-like scrolling simulation"""
        logger.info(f"Starting advanced scrolling for {duration} seconds")
        
        start_time = time.time()
        scroll_patterns = [
            {'type': 'slow_reading', 'speed': 0.3, 'distance': (100, 300), 'pause': (1.0, 2.5)},
            {'type': 'browsing', 'speed': 0.6, 'distance': (300, 600), 'pause': (0.5, 1.5)},
            {'type': 'skimming', 'speed': 0.8, 'distance': (500, 900), 'pause': (0.2, 0.8)},
            {'type': 'detailed_read', 'speed': 0.2, 'distance': (50, 200), 'pause': (2.0, 4.0)}
        ]
        
        last_scroll_time = time.time()
        total_scrolls = 0
        
        while time.time() - start_time < duration:
            # Choose pattern based on time and random factors
            elapsed = time.time() - start_time
            if elapsed < duration * 0.3:
                pattern = scroll_patterns[0]  # Start with slow reading
            elif elapsed < duration * 0.7:
                pattern = random.choice(scroll_patterns[1:3])  # Mix browsing/skimming
            else:
                pattern = random.choice(scroll_patterns)  # Random mix
            
            # Calculate scroll parameters
            min_dist, max_dist = pattern['distance']
            scroll_distance = random.randint(min_dist, max_dist)
            
            # Occasionally scroll up (15% chance)
            if random.random() < 0.15:
                scroll_distance = -scroll_distance // 2
                logger.debug("Scrolling up briefly")
            
            # Execute scroll
            driver.execute_script(f"""
                window.scrollBy({{
                    top: {scroll_distance},
                    behavior: 'smooth'
                }});
            """)
            total_scrolls += 1
            
            # Pattern-appropriate pause
            min_pause, max_pause = pattern['pause']
            pause_time = random.uniform(min_pause, max_pause)
            time.sleep(pause_time)
            
            # Simulate reading behavior occasionally
            if random.random() < 0.25:
                self.simulate_reading_behavior(driver)
            
            # Occasionally move mouse randomly
            if random.random() < 0.2:
                self.random_mouse_movement(driver)
            
            last_scroll_time = time.time()
        
        logger.info(f"Scrolling completed: {total_scrolls} scrolls in {duration}s")
        return total_scrolls

    def random_mouse_movement(self, driver):
        """Random mouse movement simulation"""
        try:
            actions = ActionChains(driver)
            # Move to random position on screen
            x = random.randint(100, 500)
            y = random.randint(100, 300)
            actions.move_by_offset(x, y)
            actions.perform()
            time.sleep(random.uniform(0.1, 0.5))
            actions.move_by_offset(-x, -y)
            actions.perform()
        except Exception:
            pass

    def safe_search_click(self, driver, query, target_domain, max_retries=3):
        """Safe search and click with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Search attempt {attempt + 1} for: {query}")
                
                # Perform search
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                driver.get(search_url)
                
                # Wait for results with a more reliable selector
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[jscontroller='SC7lYd']"))
                )
                
                self.human_delay(2, 4)
                
                # Find target link using a more specific selector
                links = driver.find_elements(By.CSS_SELECTOR, "a[jsname='UWckNb']")
                for i, link in enumerate(links[:10]):  # Check first 10 results
                    try:
                        href = link.get_attribute('href')
                        if href and target_domain in href:
                            logger.info(f"Found target at position {i + 1}: {href}")
                            
                            # Simulate reading before clicking
                            self.simulate_reading_behavior(driver, link)
                            
                            # Click the link
                            driver.execute_script("arguments[0].click();", link)
                            return href, i + 1
                    except Exception as e:
                        logger.warning(f"Error checking link {i}: {str(e)}")
                        continue
                
                # If not found, retry
                if attempt < max_retries - 1:
                    logger.info(f"Target not found, retrying... ({attempt + 1}/{max_retries})")
                    self.human_delay(3, 6)
                    
            except Exception as e:
                logger.error(f"Search attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    self.human_delay(5, 10)
        
        raise Exception(f"Target domain '{target_domain}' not found in search results after {max_retries} attempts")

    def execute_search_flow(self, query, target_domain, scroll_duration=8):
        """Main execution flow with comprehensive error handling"""
        driver = None
        session_data = {
            'success': False,
            'session_id': f"session_{int(time.time())}_{random.randint(1000, 9999)}",
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'target_domain': target_domain,
            'scroll_duration': scroll_duration,
            'steps': [],
            'metrics': {},
            'error': None
        }
        
        try:
            logger.info(f"Starting search flow: {query} -> {target_domain}")
            
            # Step 1: Initialize driver
            session_data['steps'].append({
                'step': 'initialization',
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            })
            
            driver = self.setup_driver()
            session_data['steps'][-1]['status'] = 'completed'
            
            # Step 2: Perform search and click
            session_data['steps'].append({
                'step': 'search_execution',
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            })
            
            target_url, position = self.safe_search_click(driver, query, target_domain)
            session_data['steps'][-1].update({
                'status': 'completed',
                'target_url': target_url,
                'search_position': position
            })
            
            # Step 3: Wait for page load
            session_data['steps'].append({
                'step': 'page_loading',
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            })
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.human_delay(2, 3)
            session_data['steps'][-1]['status'] = 'completed'
            session_data['final_url'] = driver.current_url
            
            # Step 4: Advanced scrolling
            session_data['steps'].append({
                'step': 'behavior_simulation',
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            })
            
            scroll_count = self.advanced_scrolling(driver, scroll_duration)
            session_data['steps'][-1].update({
                'status': 'completed',
                'scroll_actions': scroll_count
            })
            
            # Step 5: Success
            session_data['success'] = True
            session_data['metrics'] = {
                'total_duration': round(time.time() - time.mktime(
                    datetime.strptime(session_data['steps'][0]['timestamp'], '%Y-%m-%dT%H:%M:%S.%f').timetuple()
                ), 2),
                'steps_completed': len([s for s in session_data['steps'] if s['status'] == 'completed']),
                'final_page_title': driver.title
            }
            
            logger.info(f"Search flow completed successfully: {session_data['session_id']}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Search flow failed: {error_msg}")
            session_data['error'] = error_msg
            session_data['steps'].append({
                'step': 'error_handling',
                'status': 'failed',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("Driver closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing driver: {str(e)}")
        
        return session_data

# Flask Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')

# Initialize bot
search_bot = SearchBot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/search', methods=['POST'])
def api_search():
    start_time = time.time()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'code': 'NO_DATA'
            }), 400
        
        # Validate inputs
        query = data.get('query', '').strip()
        website = data.get('website', '').strip()
        scroll_duration = min(max(int(data.get('scroll_duration', 8)), 3), 30)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required',
                'code': 'MISSING_QUERY'
            }), 400
        
        if not website:
            return jsonify({
                'success': False,
                'error': 'Target website is required', 
                'code': 'MISSING_WEBSITE'
            }), 400
        
        # Clean website input
        website = website.replace('https://', '').replace('http://', '').split('/')[0]
        
        logger.info(f"API Request: '{query}' -> '{website}' ({scroll_duration}s)")
        
        # Execute search flow
        result = search_bot.execute_search_flow(query, website, scroll_duration)
        
        # Calculate response time
        response_time = round(time.time() - start_time, 2)
        
        response_data = {
            'success': result['success'],
            'data': result,
            'response_time': response_time
        }
        
        status_code = 200 if result['success'] else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR',
            'response_time': round(time.time() - start_time, 2)
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False, 
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    app.run(host='0.0.0.0', port=port, debug=debug)

