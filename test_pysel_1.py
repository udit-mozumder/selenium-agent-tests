# test_acdc_device_serial_number.py

# Import standard libraries
import os
from datetime import datetime

# Import third-party libraries
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Helper function to capture screenshots on failure
def capture_screenshot(driver, name):
    os.makedirs("screenshots", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")

# Pytest fixture to initialize and teardown the WebDriver
@pytest.fixture
def driver():
    # Setup: Initialize headless Chrome WebDriver using webdriver-manager
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    yield driver
    # Teardown: Quit the driver after test
    driver.quit()

# Helper function to login to ACDC application
def login(driver, base_url, username, password):
    wait = WebDriverWait(driver, 20)
    driver.get(base_url)
    # TODO: Replace the following locators with stable data-testid or name if available
    username_field = wait.until(EC.visibility_of_element_located((By.NAME, "username")))
    password_field = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
    username_field.clear()
    username_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)
    # Click login button
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]")))
    login_btn.click()
    # Wait for dashboard or device management section to load
    # TODO: Replace with a more stable locator if available
    wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Device Management')]")))

# Test Case TC-001: Prevent Serial Number Change for Any Device in ACDC
def test_prevent_serial_number_change_any_device(driver):
    """
    Verify that users are unable to change the serial number of any device in ACDC, regardless of collection status.
    """
    base_url = os.getenv("ACDC_URL", "https://acdc.example.com")
    username = os.getenv("ACDC_USERNAME", "testuser")
    password = os.getenv("ACDC_PASSWORD", "testpass")
    serial_number = "SN123456"

    wait = WebDriverWait(driver, 20)
    try:
        # Login to ACDC
        login(driver, base_url, username, password)

        # Navigate to device management section
        # TODO: Replace with stable locator
        device_mgmt_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Device Management')]")))
        device_mgmt_link.click()

        # Select an existing device by serial number
        # TODO: Replace with stable locator
        device_row = wait.until(EC.visibility_of_element_located((By.XPATH, f"//tr[td[contains(text(),'{serial_number}')]]")))
        device_row.click()

        # Attempt to edit the serial number field
        # TODO: Replace with stable locator
        serial_field = wait.until(EC.visibility_of_element_located((By.NAME, "serial_number")))
        # Try to edit the field (should be disabled or blocked)
        editable = serial_field.is_enabled()
        # Try to send keys anyway
        try:
            serial_field.clear()
            serial_field.send_keys("SN000000")
        except Exception:
            # Field may be disabled or readonly
            pass

        # Try to save changes
        # TODO: Replace with stable locator
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Save')]")))
        save_btn.click()

        # Assertion: Serial number field is disabled or error is shown
        # Prefer disabled field check
        assert not editable or "disabled" in serial_field.get_attribute("class").lower() or serial_field.get_attribute("readonly"), \
            "Serial number field should be disabled or readonly"

        # Check for error message
        # TODO: Replace with stable locator
        error_msg = None
        try:
            error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Serial number cannot be changed')]")))
        except Exception:
            pass
        assert error_msg is not None or not editable, "System should prevent serial number change and show an error or disable the field"

    except Exception as e:
        capture_screenshot(driver, "TC001_prevent_serial_number_change")
        raise

# Test Case TC-002: Serial Number Change Not Allowed for Devices Not Collected
def test_serial_number_change_not_allowed_not_collected(driver):
    """
    Ensure that even for devices that have not been collected, users cannot change the serial number.
    """
    base_url = os.getenv("ACDC_URL", "https://acdc.example.com")
    username = os.getenv("ACDC_USERNAME", "testuser")
    password = os.getenv("ACDC_PASSWORD", "testpass")
    serial_number = "SN987654"

    wait = WebDriverWait(driver, 20)
    try:
        # Login to ACDC
        login(driver, base_url, username, password)

        # Navigate to device management section
        device_mgmt_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Device Management')]")))
        device_mgmt_link.click()

        # Locate device with status "Not Collected"
        device_row = wait.until(EC.visibility_of_element_located((By.XPATH, f"//tr[td[contains(text(),'{serial_number}') and following-sibling::td[contains(text(),'Not Collected')]]]")))
        device_row.click()

        # Attempt to edit the serial number
        serial_field = wait.until(EC.visibility_of_element_located((By.NAME, "serial_number")))
        editable = serial_field.is_enabled()
        try:
            serial_field.clear()
            serial_field.send_keys("SN000000")
        except Exception:
            pass

        # Try to save changes
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Save')]")))
        save_btn.click()

        # Assertion: Serial number field is disabled or error is shown
        assert not editable or "disabled" in serial_field.get_attribute("class").lower() or serial_field.get_attribute("readonly"), \
            "Serial number field should be disabled or readonly for Not Collected devices"

        error_msg = None
        try:
            error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Serial number cannot be changed')]")))
        except Exception:
            pass
        assert error_msg is not None or not editable, "System should prevent serial number change and show an error or disable the field"

    except Exception as e:
        capture_screenshot(driver, "TC002_serial_number_change_not_allowed_not_collected")
        raise

# Test Case TC-003: Remove RM Dependency for Serial Number Change
def test_no_rm_dependency_on_serial_number_change(driver):
    """
    Verify that the system does not check RM (Resource Management) dependencies when attempting to change a device's serial number.
    """
    base_url = os.getenv("ACDC_URL", "https://acdc.example.com")
    username = os.getenv("ACDC_USERNAME", "testuser")
    password = os.getenv("ACDC_PASSWORD", "testpass")
    serial_number = "SN123456"

    wait = WebDriverWait(driver, 20)
    try:
        # Login to ACDC
        login(driver, base_url, username, password)

        # Navigate to device management section
        device_mgmt_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Device Management')]")))
        device_mgmt_link.click()

        # Select any device
        device_row = wait.until(EC.visibility_of_element_located((By.XPATH, f"//tr[td[contains(text(),'{serial_number}')]]")))
        device_row.click()

        # Attempt to edit the serial number
        serial_field = wait.until(EC.visibility_of_element_located((By.NAME, "serial_number")))
        try:
            serial_field.clear()
            serial_field.send_keys("SN000000")
        except Exception:
            pass

        # Try to save changes
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Save')]")))
        save_btn.click()

        # Assertion: No RM dependency error is shown
        rm_error = None
        try:
            rm_error = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'RM dependency')]")))
        except Exception:
            pass
        assert rm_error is None, "No RM dependency error should be shown"
        # Serial number change should still be blocked
        error_msg = None
        try:
            error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Serial number cannot be changed')]")))
        except Exception:
            pass
        assert error_msg is not None, "Serial number change should be blocked regardless of RM status"

    except Exception as e:
        capture_screenshot(driver, "TC003_no_rm_dependency_on_serial_number_change")
        raise

# Test Case TC-004: Remove All RM Dependencies in Device Edit Workflow
def test_remove_all_rm_dependencies_in_device_edit_workflow(driver):
    """
    Ensure that all RM dependencies are removed from the device edit workflow in ACDC.
    """
    base_url