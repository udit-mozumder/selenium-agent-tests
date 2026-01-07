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
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

# Mark these tests to be skipped in CI environment as they require real application UI
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class TestACDCDeviceManagement:
    """
    Test suite for ACDC Device Management system focusing on serial number change restrictions.
    These tests verify that serial numbers cannot be changed for devices regardless of collection status.
    """
    
    @pytest.fixture
    def driver(self):
        """
        Setup fixture to initialize the WebDriver with appropriate options.
        Returns the driver instance and handles cleanup after tests.
        """
        # Set up Chrome options for headless execution
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the Chrome WebDriver using webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait and maximize window
        driver.maximize_window()
        
        # Create a WebDriverWait instance for explicit waits
        driver.wait = WebDriverWait(driver, 20)
        
        # Return the driver instance
        yield driver
        
        # Cleanup after test execution
        driver.quit()
    
    @pytest.fixture
    def acdc_login(self, driver):
        """
        Fixture to handle login to the ACDC system.
        Assumes environment variables for credentials or uses defaults.
        """
        # Get base URL and credentials from environment variables or use defaults
        base_url = os.getenv("ACDC_URL", "https://acdc-example.com")
        username = os.getenv("ACDC_USERNAME", "test_user")
        password = os.getenv("ACDC_PASSWORD", "test_password")
        
        try:
            # Navigate to the login page
            driver.get(base_url)
            
            # Wait for the login form to be visible
            # TODO: Replace with data-testid when available
            username_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "username"))
            )
            password_field = driver.find_element(By.ID, "password")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            # TODO: Replace with data-testid when available
            login_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]")
            )
            login_button.click()
            
            # Wait for successful login (dashboard or home page)
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")
            )
            
            # Return True if login successful
            return True
        except Exception as e:
            # Capture screenshot on failure
            self.capture_screenshot(driver, "login_failure")
            # Re-raise the exception
            raise e
    
    def navigate_to_device_management(self, driver):
        """
        Helper method to navigate to the device management section.
        """
        try:
            # TODO: Replace with data-testid when available
            device_mgmt_link = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")
            )
            device_mgmt_link.click()
            
            # Wait for the device management page to load
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Device Management')]")
            )
        except Exception as e:
            self.capture_screenshot(driver, "navigation_failure")
            raise e
    
    def select_device_by_serial(self, driver, serial_number):
        """
        Helper method to select a device by its serial number.
        """
        try:
            # Search for the device by serial number
            # TODO: Replace with data-testid when available
            search_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "device-search"))
            )
            search_field.clear()
            search_field.send_keys(serial_number)
            
            # Click search button
            search_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]")
            )
            search_button.click()
            
            # Wait for search results and click on the device
            device_row = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//tr[contains(., '{serial_number}')]")
            )
            device_row.click()
            
            # Wait for device details to load
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Device Details')]")
            )
        except Exception as e:
            self.capture_screenshot(driver, "device_selection_failure")
            raise e
    
    def attempt_edit_serial_number(self, driver, new_serial):
        """
        Helper method to attempt editing a device's serial number.
        Returns a tuple: (is_editable, error_message)
        """
        try:
            # Click edit button
            # TODO: Replace with data-testid when available
            edit_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")
            )
            edit_button.click()
            
            # Wait for edit form to appear
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Edit Device')]")
            )
            
            # Try to locate the serial number field
            serial_field = driver.wait.until(
                EC.presence_of_element_located((By.ID, "serial-number"))
            )
            
            # Check if the field is disabled
            is_disabled = serial_field.get_attribute("disabled") == "true"
            
            error_message = None
            
            # If not disabled, try to edit it
            if not is_disabled:
                try:
                    serial_field.clear()
                    serial_field.send_keys(new_serial)
                    
                    # Try to save changes
                    save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
                    save_button.click()
                    
                    # Check for error message
                    try:
                        error_element = driver.wait.until(
                            EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                        )
                        error_message = error_element.text
                    except TimeoutException:
                        # No error message found
                        pass
                except ElementNotInteractableException:
                    # Field is not interactable
                    is_disabled = True
            
            # Return results
            return (not is_disabled, error_message)
        except Exception as e:
            self.capture_screenshot(driver, "edit_attempt_failure")
            raise e
    
    def delete_device(self, driver):
        """
        Helper method to delete a device.
        """
        try:
            # Click delete button
            delete_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete')]")
            )
            delete_button.click()
            
            # Confirm deletion in modal
            confirm_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]")
            )
            confirm_button.click()
            
            # Wait for success message
            driver.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
            )
            
            return True
        except Exception as e:
            self.capture_screenshot(driver, "delete_failure")
            raise e
    
    def add_new_device(self, driver, serial_number):
        """
        Helper method to add a new device with the given serial number.
        """
        try:
            # Click add device button
            add_button = driver.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Device')]")
            )
            add_button.click()
            
            # Wait for add form to appear
            driver.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Add Device')]")
            )
            
            # Fill in the serial number
            serial_field = driver.wait.until(
                EC.visibility_of_element_located((By.ID, "serial-number"))
            )
            serial_field.clear()
            serial_field.send_keys(serial_number)
            
            # Fill in other required fields (example)
            name_field = driver.find_element(By.ID, "device-name")
            name_field.clear()
            name_field.send_keys(f"Test Device {serial_number}")
            
            # Save the new device
            save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            save_button.click()
            
            # Wait for success message
            driver.wait.until(
                EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
            )
            
            return True
        except Exception as e:
            self.capture_screenshot(driver, "add_device_failure")
            raise e
    
    def capture_screenshot(self, driver, name):
        """
        Helper method to capture screenshots for debugging.
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"screenshot_{name}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"Screenshot saved as {filename}")
    
    def test_TC001_prevent_serial_change_uncollected(self, driver, acdc_login):
        """
        TC-001: Verify that the system does not allow changing the serial number for a device,
        even if the device has not been collected.
        """
        # Navigate to device management
        self.navigate_to_device_management(driver)
        
        # Select a device that has not been collected
        self.select_device_by_serial(driver, "SN12345")
        
        # Attempt to edit the serial number
        is_editable, error_message = self.attempt_edit_serial_number(driver, "SN12345-NEW")
        
        # Assert that the serial number is not editable or an error message is shown
        assert not is_editable or error_message is not None, "Serial number should not be editable for uncollected devices"