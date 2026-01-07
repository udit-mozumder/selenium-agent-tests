import pytest
import time
import json
import requests
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Skip these tests in CI environment as they require real application UI
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("acdc_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestSerialNumberChangeRestriction(object):
    """Test suite for verifying serial number change restrictions in ACDC application"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment before all tests"""
        chrome_options = Options()
        if os.getenv("HEADLESS", "False").lower() == "true":
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.maximize_window()
        cls.wait = WebDriverWait(cls.driver, 15)
        cls.base_url = os.getenv("ACDC_URL", "https://acdc-application-url.com")
        cls.api_base_url = os.getenv("ACDC_API_URL", "https://acdc-api-url.com")
        cls.username = os.getenv("ACDC_USERNAME", "test_user")
        cls.password = os.getenv("ACDC_PASSWORD", "test_password")
        cls.api_token = os.getenv("ACDC_API_TOKEN", "test_api_token")
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        if cls.driver:
            cls.driver.quit()
    
    def setup_method(self):
        """Set up before each test method"""
        self.login()
    
    def teardown_method(self):
        """Clean up after each test method"""
        # Return to home page or perform other cleanup
        self.driver.get(self.base_url)
    
    def login(self):
        """Log in to the ACDC application"""
        logger.info("Logging in to ACDC application")
        self.driver.get(f"{self.base_url}/login")
        
        try:
            # Wait for login form to be visible
            username_field = self.wait.until(
                EC.visibility_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            
            # Enter credentials and submit
            username_field.clear()
            username_field.send_keys(self.username)
            password_field.clear()
            password_field.send_keys(self.password)
            login_button.click()
            
            # Wait for successful login
            self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")
            )
            logger.info("Login successful")
        except Exception as e:
            self.take_screenshot("login_failure")
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def navigate_to_device_management(self):
        """Navigate to the device management section"""
        logger.info("Navigating to device management section")
        try:
            # Click on device management menu item
            device_mgmt_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")
            )
            device_mgmt_link.click()
            
            # Wait for the device list to load
            self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(), 'Device List')]")
            )
            logger.info("Successfully navigated to device management")
        except Exception as e:
            self.take_screenshot("navigation_failure")
            logger.error(f"Navigation to device management failed: {str(e)}")
            raise
    
    def select_device(self, serial_number):
        """Select a device with the specified serial number"""
        logger.info(f"Selecting device with serial number: {serial_number}")
        try:
            # Search for the device by serial number
            search_field = self.wait.until(
                EC.visibility_of_element_located((By.ID, "device-search"))
            )
            search_field.clear()
            search_field.send_keys(serial_number)
            search_field.send_keys(Keys.RETURN)
            
            # Wait for search results and click on the device
            device_row = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//tr[contains(., '{serial_number}')]")
            )
            device_row.click()
            
            # Wait for device details to load
            self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h3[contains(text(), 'Device Details')]")
            )
            logger.info(f"Successfully selected device: {serial_number}")
        except Exception as e:
            self.take_screenshot(f"device_selection_failure_{serial_number}")
            logger.error(f"Failed to select device {serial_number}: {str(e)}")
            raise
    
    def test_TC001_prevent_serial_number_change_uncollected(self):
        """TC-001: Verify that the system does not allow changing the serial number of an uncollected device"""
        # Test data
        serial_number = "SN12345"
        new_serial_number = "SN99999"
        
        # Navigate to device management
        self.navigate_to_device_management()
        
        # Select the uncollected device
        self.select_device(serial_number)
        
        # Attempt to edit the serial number
        result = self.attempt_edit_serial_number(new_serial_number)
        
        # Assert that the serial number field is either disabled or readonly
        # or that an error message is displayed when attempting to save
        assert result["is_disabled"] or result["is_readonly"] or result["error_message"], \
            "Serial number field should be disabled, readonly, or show error on save"