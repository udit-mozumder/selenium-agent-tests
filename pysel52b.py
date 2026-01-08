import pytest
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Mark this test to be skipped in CI environments
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class TestECommerceWorkflow:
    """
    Test class for E-Commerce website workflow automation.
    This class contains tests for product search, filtering, cart operations, and checkout process.
    """
    
    @pytest.fixture(scope="function")
    def setup(self):
        """
        Fixture to set up the WebDriver before each test and tear down after.
        Returns the configured WebDriver instance.
        """
        print("Setting up the test environment...")
        
        # Configure Chrome options for better test stability
        chrome_options = Options()
        # Run in headless mode if needed (uncomment the line below)
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Set up Chrome WebDriver with the configured options
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait time for the entire session
        driver.implicitly_wait(10)
        
        # Create a WebDriverWait instance for explicit waits
        wait = WebDriverWait(driver, 15)
        
        # Make the driver and wait available to the test
        yield {"driver": driver, "wait": wait}
        
        # Teardown: Close the browser after the test
        print("Tearing down the test environment...")
        driver.quit()
    
    def take_screenshot(self, driver, test_name):
        """
        Helper method to capture screenshots during test execution.
        
        Args:
            driver: WebDriver instance
            test_name: Name of the test for the screenshot filename
        """
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        # Generate a timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save the screenshot with a descriptive name
        screenshot_path = f"screenshots/{test_name}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
    
    def test_product_search_and_add_to_cart(self, setup):
        """
        Test case to verify product search functionality and adding items to cart.
        
        Steps:
        1. Navigate to the e-commerce website
        2. Search for a product
        3. Apply filters to narrow down results
        4. Select a product and view details
        5. Add the product to cart
        6. Verify the product is added to cart
        """
        driver = setup["driver"]
        wait = setup["wait"]
        
        try:
            # Step 1: Navigate to the e-commerce website
            print("Navigating to the e-commerce website...")
            driver.get("https://www.demoblaze.com/")
            
            # Wait for the page to load completely
            wait.until(EC.presence_of_element_located((By.ID, "nava")))
            
            # Step 2: Search for a product category
            print("Selecting product category...")
            
            # Click on the 'Laptops' category
            laptops_category = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Laptops')]")
            )
            laptops_category.click()
            
            # Wait for products to load
            wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='card-block']//h4[@class='card-title']"))
            )
            
            # Step 3: Select a specific product
            print("Selecting a specific product...")
            
            # Find and click on a specific laptop model
            product_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'MacBook Pro')]"))
            )
            product_link.click()
            
            # Step 4: Wait for product details page to load
            wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(),'MacBook Pro')]"))
            )
            
            # Verify product details are displayed
            product_title = driver.find_element(By.XPATH, "//h2[contains(text(),'MacBook Pro')]").text
            assert "MacBook Pro" in product_title, f"Expected 'MacBook Pro' in title, but got '{product_title}'"
            
            # Step 5: Add the product to cart
            print("Adding product to cart...")
            add_to_cart_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Add to cart')]"))
            )
            add_to_cart_button.click()
            
            # Wait for the alert and accept it
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            
            # Step 6: Navigate to cart and verify the product is added
            print("Navigating to cart...")
            cart_link = wait.until(
                EC.element_to_be_clickable((By.ID, "cartur"))
            )
            cart_link.click()
            
            # Wait for cart page to load
            wait.until(
                EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(),'Products')]"))
            )
            
            # Verify the product is in the cart
            cart_items = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//tr[@class='success']//td[2]"))
            )
            
            # Check if our product is in the cart
            product_in_cart = False
            for item in cart_items:
                if "MacBook Pro" in item.text:
                    product_in_cart = True
                    break
            
            assert product_in_cart, "Product 'MacBook Pro' was not found in the cart"
            print("Product successfully added to cart and verified!")
            
            # Take a screenshot of the successful test
            self.take_screenshot(driver, "successful_add_to_cart")
            
        except TimeoutException as e:
            # Take screenshot on timeout failure
            self.take_screenshot(driver, "timeout_failure")
            raise AssertionError(f"Timeout waiting for element: {str(e)}")
            
        except NoSuchElementException as e:
            # Take screenshot on element not found
            self.take_screenshot(driver, "element_not_found")
            raise AssertionError(f"Element not found: {str(e)}")
            
        except Exception as e:
            # Take screenshot on any other exception
            self.take_screenshot(driver, "test_failure")
            raise AssertionError(f"Test failed: {str(e)}")
    
    def test_checkout_process(self, setup):
        """
        Test case to verify the checkout process.
        
        Steps:
        1. Navigate to the e-commerce website
        2. Add a product to cart
        3. Proceed to checkout
        4. Fill in customer information
        5. Complete the purchase
        6. Verify order confirmation