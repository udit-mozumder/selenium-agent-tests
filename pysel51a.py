import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Mark test to be skipped in CI environment
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class TestAuthentication:
    """
    Test class for authentication functionality.
    This class contains tests related to login, logout, and authentication error scenarios.
    """
    
    @pytest.fixture(scope="function")
    def driver(self):
        """
        Fixture to initialize and configure the WebDriver.
        Returns a configured WebDriver instance and ensures proper cleanup after test.
        """
        # Set up Chrome options for better test stability and performance
        chrome_options = Options()
        
        # Run in headless mode if needed (uncomment for CI environments)
        # chrome_options.add_argument("--headless")
        
        # Additional options to improve stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize Chrome WebDriver with the configured options
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait time for better element detection
        driver.implicitly_wait(10)
        
        # Maximize window for consistent element visibility
        driver.maximize_window()
        
        # Provide the driver to the test
        yield driver
        
        # Cleanup after test completes
        driver.quit()
    
    @pytest.fixture(scope="function")
    def wait(self, driver):
        """
        Fixture to provide a WebDriverWait instance.
        This allows for explicit waits in the tests.
        """
        return WebDriverWait(driver, 15)
    
    def take_screenshot(self, driver, test_name):
        """
        Helper method to capture screenshots on test failure.
        
        Args:
            driver: WebDriver instance
            test_name: Name of the test for the screenshot filename
        """
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        # Generate a timestamp for unique filenames
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Save the screenshot with a descriptive name
        screenshot_path = f"screenshots/{test_name}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
    
    def test_successful_login(self, driver, wait):
        """
        Test case to verify successful login with valid credentials.
        
        Steps:
        1. Navigate to the login page
        2. Enter valid username and password
        3. Click the login button
        4. Verify successful login by checking for dashboard elements
        """
        try:
            # Navigate to the application login page
            driver.get("https://example.com/login")
            
            # Find username field and enter valid username
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "email")))
            username_field.clear()
            username_field.send_keys(os.getenv("TEST_USERNAME", "valid_user@example.com"))
            
            # Find password field and enter valid password
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(os.getenv("TEST_PASSWORD", "valid_password"))
            
            # Click the login button
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in') or contains(@type, 'submit')]")
            login_button.click()
            
            # Wait for dashboard to load, confirming successful login
            dashboard_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")))
            
            # Assert that we're successfully logged in
            assert dashboard_element.is_displayed(), "Dashboard element not displayed after login"
            assert "dashboard" in driver.current_url.lower(), "URL does not contain 'dashboard' after login"
            
        except (TimeoutException, NoSuchElementException, AssertionError) as e:
            # Take screenshot on failure for debugging
            self.take_screenshot(driver, "login_failure")
            # Re-raise the exception with additional context
            raise AssertionError(f"Login test failed: {str(e)}")
    
    def test_invalid_email_format(self, driver, wait):
        """
        Test case to verify error handling when a URL is provided instead of an email.
        
        Steps:
        1. Navigate to the login page
        2. Enter a URL in the email field
        3. Enter any password
        4. Click the login button
        5. Verify appropriate error message is displayed
        """
        try:
            # Navigate to the application login page
            driver.get("https://example.com/login")
            
            # Find username field and enter a URL instead of email
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "email")))
            username_field.clear()
            username_field.send_keys("https://hp-jira.external.hp.com")
            
            # Find password field and enter any password
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys("any_password")
            
            # Click the login button
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in') or contains(@type, 'submit')]")
            login_button.click()
            
            # Wait for error message to appear
            error_message = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
            ))
            
            # Assert that appropriate error message is displayed
            assert error_message.is_displayed(), "Error message not displayed for invalid email format"
            assert "valid email" in error_message.text.lower() or "invalid email" in error_message.text.lower(), \
                "Error message does not indicate email format issue"
            
        except (TimeoutException, NoSuchElementException, AssertionError) as e:
            # Take screenshot on failure for debugging
            self.take_screenshot(driver, "invalid_email_failure")
            # Re-raise the exception with additional context
            raise AssertionError(f"Invalid email format test failed: {str(e)}")
    
    def test_empty_credentials(self, driver, wait):
        """
        Test case to verify error handling when login is attempted with empty credentials.
        
        Steps:
        1. Navigate to the login page
        2. Leave username and password fields empty
        3. Click the login button
        4. Verify appropriate error messages are displayed
        """
        try:
            # Navigate to the application login page
            driver.get("https://example.com/login")
            
            # Find username and password fields and ensure they're empty
            username_field = wait.until(EC.visibility_of_element_located((By.ID, "email")))
            username_field.clear()
            
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            
            # Click the login button
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in') or contains(@type, 'submit')]")
            login_button.click()
            
            # Check for error messages
            error_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
            
            # Assert that error messages are displayed
            assert len(error_messages) > 0, "No error messages displayed for empty credentials"
            
            # Check content of error messages
            error_text = ' '.join([msg.text for msg in error_messages]).lower()
            assert any(keyword in error_text for keyword in ["required", "empty", "fill", "provide"]), \
                "Error messages do not indicate empty field issues"
                
        except (TimeoutException, NoSuchElementException, AssertionError) as e:
            # Take screenshot on failure for debugging
            self.take_screenshot(driver, "empty_credentials_failure")
            # Re-raise the exception with additional context
            raise AssertionError(f"Empty credentials test failed: {str(e)}")