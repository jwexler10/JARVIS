"""
Web Automation Module (Phase 5B - Local Implementation)
Provides secure web automation using local Selenium WebDriver.
This replaces the Docker-based sandbox approach for systems without Docker/WSL2.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebAutomationController:
    """Controls web automation using local Selenium WebDriver."""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize Chrome WebDriver with security-focused options."""
        try:
            chrome_options = Options()
            
            # Security and privacy options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript")  # Security (can be enabled per-site)
            chrome_options.add_argument("--incognito")  # Private browsing
            chrome_options.add_argument("--disable-web-security")  # Allow cross-origin requests
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # User agent to appear as regular browser
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Try to find Chrome executable
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            if chrome_path:
                chrome_options.binary_location = chrome_path
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("✅ Web automation controller initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize web driver: {e}")
            self.driver = None
            return False
    
    def is_active(self):
        """Check if the browser session is active."""
        return self.driver is not None
    
    def open_page(self, url):
        """Open a web page."""
        if not self.is_active():
            if not self._setup_driver():
                return {"error": "Browser initialization failed"}
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.driver.get(url)
            time.sleep(2)  # Allow page to load
            
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title
            }
        except Exception as e:
            return {"error": f"Failed to open page: {str(e)}"}
    
    def get_page_title(self):
        """Get the current page title."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            return {"title": self.driver.title}
        except Exception as e:
            return {"error": f"Failed to get title: {str(e)}"}
    
    def get_page_url(self):
        """Get the current page URL."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            return {"url": self.driver.current_url}
        except Exception as e:
            return {"error": f"Failed to get URL: {str(e)}"}
    
    def extract_text(self, selector):
        """Extract text from elements matching the CSS selector."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if not elements:
                return {"error": f"No elements found for selector: {selector}"}
            
            texts = [element.text.strip() for element in elements if element.text.strip()]
            return {"texts": texts}
        except Exception as e:
            return {"error": f"Failed to extract text: {str(e)}"}
    
    def click_element(self, selector):
        """Click an element using CSS selector."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            time.sleep(1)  # Allow action to complete
            return {"success": True, "message": f"Clicked element: {selector}"}
        except TimeoutException:
            return {"error": f"Element not clickable: {selector}"}
        except Exception as e:
            return {"error": f"Failed to click element: {str(e)}"}
    
    def fill_input(self, selector, text):
        """Fill an input field with text."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.clear()
            element.send_keys(text)
            return {"success": True, "message": f"Filled input {selector} with text"}
        except Exception as e:
            return {"error": f"Failed to fill input: {str(e)}"}
    
    def wait_for_element(self, selector, timeout=10):
        """Wait for an element to be present."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return {"success": True, "message": f"Element found: {selector}"}
        except TimeoutException:
            return {"error": f"Element not found within {timeout} seconds: {selector}"}
        except Exception as e:
            return {"error": f"Error waiting for element: {str(e)}"}
    
    def get_element_attribute(self, selector, attribute):
        """Get an attribute value from an element."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            value = element.get_attribute(attribute)
            return {"attribute": attribute, "value": value}
        except NoSuchElementException:
            return {"error": f"Element not found: {selector}"}
        except Exception as e:
            return {"error": f"Failed to get attribute: {str(e)}"}
    
    def take_screenshot(self, filename=None):
        """Take a screenshot of the current page."""
        if not self.is_active():
            return {"error": "Browser not active"}
        
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            # Save to current directory
            screenshot_path = os.path.join(os.getcwd(), filename)
            self.driver.save_screenshot(screenshot_path)
            return {"success": True, "path": screenshot_path}
        except Exception as e:
            return {"error": f"Failed to take screenshot: {str(e)}"}
    
    def close_browser(self):
        """Close the browser session."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.wait = None
                return {"success": True, "message": "Browser closed"}
            except Exception as e:
                return {"error": f"Error closing browser: {str(e)}"}
        return {"message": "Browser was not active"}

# Global instance
_web_controller = None

def get_web_controller():
    """Get or create the global web controller instance."""
    global _web_controller
    if _web_controller is None:
        _web_controller = WebAutomationController()
    return _web_controller

# Public API functions for tools.py
def open_page(url):
    """Open a web page."""
    controller = get_web_controller()
    return controller.open_page(url)

def click_element(selector):
    """Click an element using CSS selector."""
    controller = get_web_controller()
    return controller.click_element(selector)

def extract_text(selector):
    """Extract text from elements matching the CSS selector."""
    controller = get_web_controller()
    return controller.extract_text(selector)

def fill_input(selector, text):
    """Fill an input field with text."""
    controller = get_web_controller()
    return controller.fill_input(selector, text)

def get_page_title():
    """Get the current page title."""
    controller = get_web_controller()
    return controller.get_page_title()

def get_page_url():
    """Get the current page URL."""
    controller = get_web_controller()
    return controller.get_page_url()

def wait_for_element(selector, timeout=10):
    """Wait for an element to be present."""
    controller = get_web_controller()
    return controller.wait_for_element(selector, timeout)

def get_element_attribute(selector, attribute):
    """Get an attribute value from an element."""
    controller = get_web_controller()
    return controller.get_element_attribute(selector, attribute)

def take_screenshot(filename=None):
    """Take a screenshot of the current page."""
    controller = get_web_controller()
    return controller.take_screenshot(filename)

def close_browser():
    """Close the browser session."""
    controller = get_web_controller()
    return controller.close_browser()

if __name__ == "__main__":
    # Test the web automation
    print("🧪 Testing web automation...")
    
    result = open_page("https://www.google.com")
    print(f"Open page result: {result}")
    
    if "success" in result:
        title_result = get_page_title()
        print(f"Page title: {title_result}")
        
        # Take a screenshot
        screenshot_result = take_screenshot("test_screenshot.png")
        print(f"Screenshot result: {screenshot_result}")
    
    close_browser()
    print("✅ Test completed")
