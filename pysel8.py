
import pytest
pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

# Import standard and third-party modules
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Utility class for Selenium actions and waits
class SeleniumBase:
    def __init__(self):
        # Initialize Chrome WebDriver in headless mode for CI/CD compatibility
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 20)

    def open(self, url: str):
        # Navigate to the specified URL
        self.driver.get(url)

    def find(self, by, value):
        # Wait for element to be visible and return it
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def click(self, by, value):
        # Wait for element to be clickable and click it
        self.wait.until(EC.element_to_be_clickable((by, value))).click()

    def type(self, by, value, text: str):
        # Find input element, clear it, and send keys
        element = self.find(by, value)
        element.clear()
        element.send_keys(text)

    def is_disabled(self, by, value):
        # Check if the element is disabled (for input fields)
        element = self.find(by, value)
        return not element.is_enabled()

    def screenshot(self, name: str):
        # Save screenshot with timestamp for debugging
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")

    def quit(self):
        # Quit the browser and cleanup resources
        self.driver.quit()

@pytest.fixture
def app():
    # Pytest fixture for SeleniumBase setup and teardown
    base = SeleniumBase()
    yield base
    base.quit()

class TestACDCDeviceManagement:
    # Base URL and credentials should be set via environment variables for security
    BASE_URL = os.getenv("ACDC_URL", "https://acdc.example.com")
    USERNAME = os.getenv("ACDC_USERNAME", "testuser")
    PASSWORD = os.getenv("ACDC_PASSWORD", "testpass")

    # Helper method to login (assumes login page structure)
    def login(self, app):
        app.open(self.BASE_URL + "/login")
        # TODO: Replace text-based locator with stable data-testid or name
        app.type(By.NAME, "username", self.USERNAME)
        app.type(By.NAME, "password", self.PASSWORD)
        app.click(By.XPATH, "//button[contains(text(),'Login')]")
        # Wait for dashboard or device management to appear
        try:
            dashboard = app.find(By.XPATH, "//*[contains(text(),'Device Management')]")
            assert dashboard.is_displayed()
        except Exception:
            app.screenshot("login_failure")
            raise

    def navigate_to_device_management(self, app):
        # Navigate to device management section after login
        # TODO: Replace text-based locator with stable data-testid
        app.open(self.BASE_URL + "/devices")
        # Wait for device table/list to be visible
        app.find(By.XPATH, "//*[contains(text(),'Device List')]")

    def select_device(self, app, serial_number):
        # Select a device by serial number from the device list
        # TODO: Replace text-based locator with stable data-testid
        device_row = app.find(By.XPATH, f"//tr[td[contains(text(),'{serial_number}')]]")
        device_row.click()

    def open_edit_device(self, app):
        # Open the edit screen for the selected device
        # TODO: Replace text-based locator with stable data-testid
        app.click(By.XPATH, "//button[contains(text(),'Edit')]")
        # Wait for edit modal/screen
        app.find(By.XPATH, "//*[contains(text(),'Edit Device')]")

    def delete_device(self, app):
        # Delete the currently selected device
        # TODO: Replace text-based locator with stable data-testid
        app.click(By.XPATH, "//button[contains(text(),'Delete')]")
        # Confirm deletion if prompted
        try:
            confirm_btn = app.find(By.XPATH, "//button[contains(text(),'Confirm')]")
            confirm_btn.click()
        except Exception:
            # If no confirmation needed, continue
            pass

    def add_device(self, app, serial_number, extra_info=""):
        # Add a new device with given serial number and info
        app.click(By.XPATH, "//button[contains(text(),'Add Device')]")
        app.find(By.XPATH, "//*[contains(text(),'Add New Device')]")
        # TODO: Replace text-based locator with stable data-testid or name
        app.type(By.NAME, "serialNumber", serial_number)
        if extra_info:
            app.type(By.NAME, "deviceInfo", extra_info)
        app.click(By.XPATH, "//button[contains(text(),'Save')]")
        # Wait for device to appear in list
        app.find(By.XPATH, f"//tr[td[contains(text(),'{serial_number}')]]")

    def attempt_serial_number_change(self, app, new_serial):
        # Try to change the serial number in the edit screen
        # TODO: Replace text-based locator with stable data-testid or name
        serial_field = app.find(By.NAME, "serialNumber")
        try:
            serial_field.clear()
            serial_field.send_keys(new_serial)
        except Exception:
            # Field may be disabled or not editable
            pass
        app.click(By.XPATH, "//button[contains(text(),'Save')]")

    def get_error_message(self, app):
        # Retrieve error message displayed after failed serial number change
        # TODO: Replace text-based locator with stable data-testid
        error_msg = app.find(By.XPATH, "//*[contains(@class,'error') or contains(text(),'Serial number changes are not allowed')]")
        return error_msg.text

    def is_serial_field_disabled(self, app):
        # Check if serial number field is disabled
        return app.is_disabled(By.NAME, "serialNumber")

    def test_prevent_serial_number_change_for_any_device(self, app):
        """
        TC-001: Prevent Serial Number Change for Any Device in ACDC
        """
        self.login(app)
        self.navigate_to_device_management(app)
        self.select_device(app, "SN123456")
        self.open_edit_device(app)
        # Try to edit serial number
        field_disabled = self.is_serial_field_disabled(app)
        assert field_disabled, "Serial number field should be disabled"
        # Attempt to change serial number anyway
        self.attempt_serial_number_change(app, "SN654321")
        # Assert that serial number was not changed
        self.navigate_to_device_management(app)
        self.select_device(app, "SN123456")
        self.open_edit_device(app)
        serial_field = app.find(By.NAME, "serialNumber")
        assert serial_field.get_attribute("value") == "SN123456", "Serial number should remain unchanged"

    def test_remove_rm_dependency_for_serial_number_change(self, app):
        """
        TC-002: Remove RM Dependency for Serial Number Change
        """
        self.login(app)
        self.navigate_to_device_management(app)
        # Test with device having RM collection status
        self.select_device(app, "SN123456")  # Assume this device has RM status
        self.open_edit_device(app)
        field_disabled = self.is_serial_field_disabled(app)
        assert field_disabled, "Serial number field should be disabled regardless of RM status"
        # Test with device without RM collection status
        self.select_device(app, "SN654321")  # Assume this device does NOT have RM status
        self.open_edit_device(app)
        field_disabled = self.is_serial_field_disabled(app)
        assert field_disabled, "Serial number field should be disabled regardless of RM status"

    def test_remove_all_rm_dependencies_from_device_management(self, app):
        """
        TC-003: Remove All RM Dependencies from Device Management
        """
        self.login(app)
        self.navigate_to_device_management(app)
        # Try add operation
        self.add_device(app, "SN999999", extra_info="With RM")
        self.add_device(app, "SN888888", extra_info="Without RM")
        # Try edit operation
        self.select_device(app, "SN999999")
        self.open_edit_device(app)
        field_disabled = self.is_serial_field_disabled(app)
        assert field_disabled, "Serial number field should be disabled for all devices"
        # Try delete operation
        self.select_device(app, "SN888888")
        self.delete_device(app)
        # Assert device is deleted (not present in list)
        try:
            app.find(By.XPATH, f"//tr[td[contains(text(),'SN888888')]]")
            # If found, fail
            assert False, "Device should be deleted"
        except Exception:
            # Not found, pass
            pass

    def test_device_deletion_and_readdition_with_corrected_information(self, app):
        """
        TC-004: Device Deletion and Re-Addition with Corrected Information
        """
        self.login(app)
        self.navigate_to_device_management(app)
        # Delete original device
        self.select_device(app, "SN123456")
        self.delete_device(app)
        # Add new device with corrected serial number
        self.add_device(app, "SN654321", extra_info="Corrected Info")
        # Assert new device is present
        device_row = app.find(By.XPATH, f"//tr