import pytest
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class TestDeviceManagement:
    """
    Pytest test suite for device management scenarios.
    """

    @pytest.fixture
    def driver(self):
        """
        Initializes and tears down Selenium WebDriver.
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)
        yield driver
        driver.quit()

    def capture_screenshot(self, driver, test_name):
        """
        Helper to capture screenshot on failure.
        """
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/{test_name}_{timestamp}.png"
        driver.save_screenshot(filename)

    def login(self, driver):
        """
        Helper to login to the application.
        """
        driver.get("https://device-management-system.example.com/login")
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.visibility_of_element_located((By.ID, "username")))
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        username = os.getenv("DMS_USERNAME", "admin")
        password = os.getenv("DMS_PASSWORD", "admin123")
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button.click()
        wait.until(EC.url_contains("dashboard"))

    def navigate_to_device_list(self, driver):
        """
        Helper to navigate to the device list page.
        """
        wait = WebDriverWait(driver, 10)
        devices_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Devices')]") ))
        devices_menu.click()
        wait.until(EC.presence_of_element_located((By.ID, "device-list-table")))

    def open_device_edit_form(self, driver, device_id="SN12345"):
        """
        Helper to open the edit form for a specific device.
        """
        self.navigate_to_device_list(driver)
        wait = WebDriverWait(driver, 10)
        edit_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//tr[contains(., '{device_id}')]//button[contains(@class, 'edit-btn')]"
        )))
        edit_button.click()
        wait.until(EC.presence_of_element_located((By.ID, "device-edit-form")))

    def test_prevent_serial_number_change(self, driver):
        """
        TC-001: Prevent Serial Number Change for Any Device.
        """
        try:
            self.login(driver)
            self.open_device_edit_form(driver, device_id="SN12345")
            wait = WebDriverWait(driver, 10)
            serial_number_field = wait.until(EC.presence_of_element_located((By.ID, "serial-number")))
            # Assert field is disabled or readonly
            assert not serial_number_field.is_enabled() or serial_number_field.get_attribute("readonly") == "true"
        except Exception:
            self.capture_screenshot(driver, "test_prevent_serial_number_change")
            raise

    def test_remove_rm_dependency_for_serial_number(self, driver):
        """
        TC-002: Remove RM Dependency for Serial Number Change.
        """
        try:
            self.login(driver)
            # Device with RM collected
            self.open_device_edit_form(driver, device_id="DeviceA")
            page_source = driver.page_source.lower()
            assert "rm approval" not in page_source
            # Device with RM not collected
            self.open_device_edit_form(driver, device_id="DeviceB")
            page_source = driver.page_source.lower()
            assert "rm approval" not in page_source
        except Exception:
            self.capture_screenshot(driver, "test_remove_rm_dependency_for_serial_number")
            raise

    def test_remove_all_rm_dependencies_for_device_editing(self, driver):
        """
        TC-003: Remove All RM Dependencies Related to Device Editing.
        """
        try:
            self.login(driver)
            for device_id in ["DeviceA", "DeviceB", "DevicePending"]:
                self.open_device_edit_form(driver, device_id=device_id)
                page_source = driver.page_source.lower()
                assert "rm approval" not in page_source
                assert "manager approval" not in page_source
        except Exception:
            self.capture_screenshot(driver, "test_remove_all_rm_dependencies_for_device_editing")
            raise

    def test_delete_device_to_correct_serial_number(self, driver):
        """
        TC-004: Delete Device to Correct Serial Number.
        """
        try:
            self.login(driver)
            self.navigate_to_device_list(driver)
            wait = WebDriverWait(driver, 10)
            delete_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//tr[contains(., 'SN00000')]//button[contains(@class, 'delete-btn')]"
            )))
            delete_button.click()
            confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]") ))
            confirm_button.click()
            success_message = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'alert-success')]"
            )))
            assert "deleted" in success_message.text.lower()
            add_button = wait.until(EC.element_to_be_clickable((By.ID, "add-device-button")))
            add_button.click()
            wait.until(EC.presence_of_element_located((By.ID, "device-create-form")))
            driver.find_element(By.ID, "device-name").send_keys("Test Device")
            driver.find_element(By.ID, "serial-number").send_keys("SN54321")
            driver.find_element(By.ID, "model").send_keys("Model X")
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            create_success = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'alert-success')]"
            )))
            assert "created" in create_success.text.lower()
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//tr[contains(., 'SN54321')]"
            )))
        except Exception:
            self.capture_screenshot(driver, "test_delete_device_to_correct_serial_number")
            raise

    def test_edit_other_device_fields(self, driver):
        """
        TC-005: Attempt to Edit Other Device Fields.
        """
        try:
            self.login(driver)
            self.open_device_edit_form(driver, device_id="SN12345")
            wait = WebDriverWait(driver, 10)
            serial_number_field = wait.until(EC.presence_of_element_located((By.ID, "serial-number")))
            assert not serial_number_field.is_enabled() or serial_number_field.get_attribute("readonly") == "true"
            name_field = driver.find_element(By.ID, "device-name")
            location_field = driver.find_element(By.ID, "location")
            description_field = driver.find_element(By.ID, "description")
            name_field.clear()
            name_field.send_keys("Updated Device Name")
            location_field.clear()
            location_field.send_keys("New Location")
            description_field.clear()
            description_field.send_keys("Updated Description")
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            success_message = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'alert-success')]"
            )))
            assert "updated" in success_message.text.lower()
        except Exception:
            self.capture_screenshot(driver, "test_edit_other_device_fields")
            raise

    def test_change_serial_number_via_api(self):
        """
        TC-006: Attempt to Change Serial Number via API.
        """
        # Mock API endpoint and token for demonstration
        api_url = os.getenv("DMS_API_URL", "https://device-management-system.example.com/api/devices/SN12345")
        token = os.getenv("DMS_API_TOKEN", "dummy-token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"serial_number": "NEW-SERIAL-999"}
        response = requests.patch(api_url, json=payload, headers=headers)
        assert response.status_code in [400, 403], "API should prevent serial number change"
        assert "cannot change serial number" in response.text.lower() or "error" in response.text.lower()

    def test_ui_feedback_when_serial_number_change_attempted(self, driver):
        """
        TC-007: UI Feedback When Serial Number Change is Attempted.
        """
        try:
            self.login(driver)
            self.open_device_edit_form(driver, device_id="SN12345")
            wait = WebDriverWait(driver, 10)
            serial_number_field = wait.until(EC.presence_of_element_located((By.ID, "serial-number")))
            # Try to interact with the field (if enabled, attempt to edit)
            if serial_number_field.is_enabled():
                serial_number_field.clear()
                serial_number_field.send_keys("NEW-SERIAL-999")
                driver.find_element(By.XPATH, "//button[@type='submit']").click()
                error_message = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'alert-danger')]"
                )))
                assert "cannot be changed" in error_message.text.lower()
            else:
                # Field is disabled, check for helper text
                helper = driver.find_element(By.ID, "serial-number-helper")
                assert "cannot be changed" in helper.text.lower() or "delete and re-add" in helper.text.lower()
        except Exception:
            self.capture_screenshot(driver, "test_ui_feedback_when_serial_number_change_attempted")
            raise
