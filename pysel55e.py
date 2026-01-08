import pytest
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Skip these tests in CI environment as they require real application UI
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class ACDCDeviceManagementTests:
    """
    Test suite for ACDC device management functionality, focusing on serial number
    change restrictions and RM dependency removal.
    """
    
    @pytest.fixture
    def driver(self):
        """
        Setup and teardown for WebDriver.
        Creates a headless Chrome browser instance and quits after test.
        """
        # Initialize Chrome options for headless execution
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Setup Chrome driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait and maximize window
        driver.maximize_window()
        
        # Create a WebDriverWait instance for explicit waits
        wait = WebDriverWait(driver, 20)
        
        # Add wait and driver to yield
        driver.wait = wait
        
        # Yield driver to test
        yield driver
        
        # Quit driver after test completes
        driver.quit()
    
    def capture_screenshot(self, driver, name):
        """
        Capture screenshot on test failure.
        
        Args:
            driver: WebDriver instance
            name: Screenshot name prefix
        """
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
    
    def login_to_acdc(self, driver):
        """
        Login to ACDC application.
        
        Args:
            driver: WebDriver instance
        """
        # Get base URL from environment or use default
        base_url = os.getenv("ACDC_URL", "https://acdc-app.example.com")
        username = os.getenv("ACDC_USERNAME", "test_user")
        password = os.getenv("ACDC_PASSWORD", "test_password")
        
        # Navigate to the application
        driver.get(base_url)
        
        try:
            # Find username field and enter username
            # TODO: Replace with data-testid when available
            username_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            # Find password field and enter password
            # TODO: Replace with data-testid when available
            password_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            # TODO: Replace text-based locator with stable data-testid
            login_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]")
            )
            login_button.click()
            
            # Wait for dashboard to load
            driver.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")
            )
        except Exception as e:
            self.capture_screenshot(driver, "login_failure")
            raise Exception(f"Login failed: {str(e)}")
    
    def navigate_to_device_management(self, driver):
        """
        Navigate to device management section.
        
        Args:
            driver: WebDriver instance
        """
        try:
            # Click on device management link/button
            # TODO: Replace text-based locator with stable data-testid
            device_mgmt_link = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")
            )
            device_mgmt_link.click()
            
            # Wait for device management page to load
            driver.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Device Management')]")
            )
        except Exception as e:
            self.capture_screenshot(driver, "navigation_failure")
            raise Exception(f"Navigation to device management failed: {str(e)}")
    
    def select_device(self, driver, serial_number):
        """
        Select a device by serial number.
        
        Args:
            driver: WebDriver instance
            serial_number: Serial number of the device to select
        """
        try:
            # Search for the device by serial number if search functionality exists
            # TODO: Replace with data-testid when available
            search_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "device-search"))
            )
            search_field.clear()
            search_field.send_keys(serial_number)
            
            # Click search button if exists
            # TODO: Replace text-based locator with stable data-testid
            search_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]")
            )
            search_button.click()
            
            # Wait for search results and click on the device
            # TODO: Replace with more stable locator when available
            device_row = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//tr[contains(., '{serial_number}')]")
            )
            device_row.click()
        except Exception as e:
            self.capture_screenshot(driver, "device_selection_failure")
            raise Exception(f"Device selection failed: {str(e)}")
    
    def attempt_edit_serial_number(self, driver, new_serial_number):
        """
        Attempt to edit the serial number of a device.
        
        Args:
            driver: WebDriver instance
            new_serial_number: New serial number to attempt to set
        
        Returns:
            tuple: (is_editable, error_message)
                is_editable: Boolean indicating if serial number field is editable
                error_message: Error message displayed (if any)
        """
        try:
            # Click edit button if exists
            # TODO: Replace text-based locator with stable data-testid
            edit_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")
            )
            edit_button.click()
            
            # Try to find serial number field
            # TODO: Replace with data-testid when available
            serial_field = driver.wait.until(
                EC.presence_of_element_located((By.ID, "serial-number"))
            )
            
            # Check if field is disabled
            is_editable = not serial_field.get_attribute("disabled")
            
            # If editable, try to change it
            error_message = None
            if is_editable:
                serial_field.clear()
                serial_field.send_keys(new_serial_number)
                
                # Try to save changes
                # TODO: Replace text-based locator with stable data-testid
                save_button = driver.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]")
                )
                save_button.click()
                
                # Check for error messages
                try:
                    error_element = driver.wait.until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                    )
                    error_message = error_element.text
                except:
                    # No error message found
                    pass
            
            return (is_editable, error_message)
        except Exception as e:
            self.capture_screenshot(driver, "edit_serial_failure")
            raise Exception(f"Attempt to edit serial number failed: {str(e)}")
    
    def test_tc001_prevent_serial_number_change(self, driver):
        """
        TC-001: Verify that ACDC does not allow any serial number changes for devices.
        """
        self.login_to_acdc(driver)
        self.navigate_to_device_management(driver)
        self.select_device(driver, "SN12345")
        
        # Attempt to edit serial number
        is_editable, error_message = self.attempt_edit_serial_number(driver, "SN12345-NEW")
        
        # Assert that either the field is not editable or an error message is shown
        assert not is_editable or error_message is not None, "Serial number should not be editable"