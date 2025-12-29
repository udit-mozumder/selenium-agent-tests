import pytest
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time

# Constants (Replace these with your actual test site and test data)
BASE_URL = "https://demowebshop.tricentis.com/"
REGISTER_EMAIL = "testuser_selenium_001@example.com"
REGISTER_PASSWORD = "TestPassword123!"

@pytest.fixture(scope="module")
def driver():
    """
    Pytest fixture to initialize and quit the Selenium WebDriver.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def wait_for_element(driver, by, value, timeout=10):
    """
    Wait for an element to be present and return it.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        pytest.fail(f"Element not found: {value}")

def test_e2e_ecommerce_flow(driver):
    """
    End-to-end test for e-commerce website:
    1. User registration
    2. Login
    3. Product search
    4. Add to cart
    5. Checkout
    """

    # 1. User Registration
    driver.get(BASE_URL)
    try:
        register_link = wait_for_element(driver, By.LINK_TEXT, "Register")
        register_link.click()
        # Fill registration form
        wait_for_element(driver, By.ID, "gender-male").click()
        driver.find_element(By.ID, "FirstName").send_keys("Test")
        driver.find_element(By.ID, "LastName").send_keys("User")
        driver.find_element(By.ID, "Email").send_keys(REGISTER_EMAIL)
        driver.find_element(By.ID, "Password").send_keys(REGISTER_PASSWORD)
        driver.find_element(By.ID, "ConfirmPassword").send_keys(REGISTER_PASSWORD)
        driver.find_element(By.ID, "register-button").click()
        # Assert registration success
        success_msg = wait_for_element(driver, By.CLASS_NAME, "result").text
        assert "Your registration completed" in success_msg
        # Logout to test login
        wait_for_element(driver, By.LINK_TEXT, "Log out").click()
    except Exception as e:
        pytest.fail(f"Registration failed: {e}")

    # 2. User Login
    try:
        login_link = wait_for_element(driver, By.LINK_TEXT, "Log in")
        login_link.click()
        driver.find_element(By.ID, "Email").send_keys(REGISTER_EMAIL)
        driver.find_element(By.ID, "Password").send_keys(REGISTER_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "input.login-button").click()
        # Assert login success
        account_link = wait_for_element(driver, By.LINK_TEXT, "My account")
        assert account_link.is_displayed()
    except Exception as e:
        pytest.fail(f"Login failed: {e}")

    # 3. Product Search
    try:
        search_box = wait_for_element(driver, By.ID, "small-searchterms")
        search_box.clear()
        search_box.send_keys("computer")
        search_box.send_keys(Keys.RETURN)
        # Wait for search results
        results = wait_for_element(driver, By.CSS_SELECTOR, ".product-item")
        assert results.is_displayed()
    except Exception as e:
        pytest.fail(f"Product search failed: {e}")

    # 4. Add to Cart
    try:
        # Click on the first product in the results
        first_product = driver.find_elements(By.CSS_SELECTOR, ".product-item .product-title a")[0]
        first_product.click()
        # Add to cart
        add_to_cart_btn = wait_for_element(driver, By.ID, "add-to-cart-button-72")
        add_to_cart_btn.click()
        # Wait for confirmation message
        cart_msg = wait_for_element(driver, By.CSS_SELECTOR, ".bar-notification.success")
        assert "The product has been added to your shopping cart" in cart_msg.text
    except Exception as e:
        pytest.fail(f"Add to cart failed: {e}")

    # 5. Checkout Process
    try:
        # Go to shopping cart
        cart_link = wait_for_element(driver, By.LINK_TEXT, "Shopping cart")
        cart_link.click()
        # Agree to terms of service
        terms_checkbox = wait_for_element(driver, By.ID, "termsofservice")
        if not terms_checkbox.is_selected():
            terms_checkbox.click()
        # Proceed to checkout
        checkout_btn = wait_for_element(driver, By.ID, "checkout")
        checkout_btn.click()
        # Billing Address
        wait_for_element(driver, By.ID, "BillingNewAddress_CountryId")
        driver.find_element(By.ID, "BillingNewAddress_CountryId").send_keys("United States")
        driver.find_element(By.ID, "BillingNewAddress_City").send_keys("New York")
        driver.find_element(By.ID, "BillingNewAddress_Address1").send_keys("123 Test Street")
        driver.find_element(By.ID, "BillingNewAddress_ZipPostalCode").send_keys("10001")
        driver.find_element(By.ID, "BillingNewAddress_PhoneNumber").send_keys("1234567890")
        driver.find_element(By.CSS_SELECTOR, "input.button-1.new-address-next-step-button").click()
        # Shipping Method
        wait_for_element(driver, By.CSS_SELECTOR, "input.button-1.shipping-method-next-step-button").click()
        # Payment Method
        wait_for_element(driver, By.CSS_SELECTOR, "input.button-1.payment-method-next-step-button").click()
        # Payment Information
        wait_for_element(driver, By.CSS_SELECTOR, "input.button-1.payment-info-next-step-button").click()
        # Confirm Order
        wait_for_element(driver, By.CSS_SELECTOR, "input.button-1.confirm-order-next-step-button").click()
        # Assert order confirmation
        confirm_msg = wait_for_element(driver, By.CSS_SELECTOR, ".section.order-completed .title").text
        assert "Your order has been successfully processed!" in confirm_msg
    except Exception as e:
        pytest.fail(f"Checkout failed: {e}")

    # End of test
    print("E2E e-commerce flow completed successfully.")