
import pytest
import time
import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests

pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

# =========================
# Base Test Utility Classes
# =========================

class ACDCTestBase:
    """Base class for ACDC system Selenium tests."""
    def __init__(self):
        self.setup_driver()
        self.base_url = os.getenv("ACDC_BASE_URL", "https://acdc-system.example.com")
        self.api_url = os.getenv("ACDC_API_URL", "https://api.acdc-system.example.com")
        self.username = os.getenv("ACDC_USERNAME", "admin")
        self.password = os.getenv("ACDC_PASSWORD", "admin123")
        self.wait = WebDriverWait(self.driver, 20)

    def setup_driver(self):
        """Initialize Chrome WebDriver with headless options."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self):
        """Login to the ACDC system UI."""
        self.driver.get(f"{self.base_url}/login")
        self.wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(self.username)
        self.wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(self.password)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]")).click()
        # Confirm login by checking dashboard
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")

    def navigate_to_device_management(self):
        """Navigate to Device Management section."""
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")).click()
        self.wait.until(EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(), 'Device Management')]")

    def search_device(self, serial_number):
        """Search for a device by serial number."""
        search_field = self.wait.until(EC.visibility_of_element_located((By.ID, "device-search")))
        search_field.clear()
        search_field.send_keys(serial_number)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]")).click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "search-results")))

    def select_device(self, serial_number):
        """Select a device from search results."""
        device_row = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[contains(., '{serial_number}')]")
        device_row.click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "device-details")))

    def open_edit_device_dialog(self):
        """Open the edit device dialog."""
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit Device')]")).click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "edit-device-dialog")))

    def attempt_serial_number_change(self, new_serial_number):
        """Attempt to change serial number in edit dialog."""
        serial_field = self.wait.until(EC.visibility_of_element_located((By.ID, "device-serial")))
        is_disabled = serial_field.get_attribute("disabled") == "true"
        if not is_disabled:
            serial_field.clear()
            serial_field.send_keys(new_serial_number)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save Changes')]")).click()
        return is_disabled

    def check_for_error_message(self):
        """Check for error message after invalid operation."""
        try:
            error_message = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "error-message")))
            return error_message.text
        except TimeoutException:
            return None

    def delete_device(self, serial_number):
        """Delete a device from the system."""
        self.search_device(serial_number)
        self.select_device(serial_number)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete Device')]")).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm Delete')]")).click()
        try:
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "success-message")))
            return True
        except TimeoutException:
            return False

    def add_device(self, device_data):
        """Add a new device to the system."""
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Device')]")).click()
        self.wait.until(EC.visibility_of_element_located((By.ID, "add-device-form")))
        self.wait.until(EC.visibility_of_element_located((By.ID, "device-name"))).send_keys(device_data["name"])
        self.wait.until(EC.visibility_of_element_located((By.ID, "device-serial"))).send_keys(device_data["serial"])
        self.wait.until(EC.visibility_of_element_located((By.ID, "device-model"))).send_keys(device_data["model"])
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]")).click()
        try:
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "success-message")))
            return True
        except TimeoutException:
            return False

    def check_serial_field_readonly(self):
        """Check if serial number field is readonly/disabled."""
        serial_field = self.wait.until(EC.visibility_of_element_located((By.ID, "device-serial")))
        return serial_field.get_attribute("readonly") == "true" or serial_field.get_attribute("disabled") == "true"

    def quit(self):
        """Cleanup and close browser."""
        self.driver.quit()

# =========================
# API Utility Functions
# =========================

def attempt_serial_number_change_api(api_url, device_id, new_serial):
    """Attempt to change serial number via API."""
    endpoint = f"{api_url}/devices/{device_id}"
    headers = {"Content-Type": "application/json"}
    payload = {"serial": new_serial}
    response = requests.put(endpoint, headers=headers, data=json.dumps(payload))
    return response

def get_device_by_serial_api(api_url, serial):
    """Get device details by serial number via API."""
    endpoint = f"{api_url}/devices?serial={serial}"
    response = requests.get(endpoint)
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def get_audit_log_api(api_url, serial):
    """Get audit logs for a device serial number."""
    endpoint = f"{api_url}/audit?serial={serial}"
    response = requests.get(endpoint)
    return response.json() if response.status_code == 200 else []

# =========================
# Pytest Fixtures
# =========================

@pytest.fixture(scope="function")
def acdc_app():
    """Fixture to provide ACDCTestBase instance and cleanup."""
    app = ACDCTestBase()
    app.login()
    yield app
    app.quit()

# =========================
# Test Cases Implementation
# =========================

class TestACDCDeviceManagement:

    def test_tc_001_prevent_serial_number_change_ui(self, acdc_app):
        """
        TC-001: Prevent Serial Number Change for Any Device in ACDC
        """
        acdc_app.navigate_to_device_management()
        acdc_app.search_device("SN12345")
        acdc_app.select_device("SN12345")
        acdc_app.open_edit_device_dialog()
        is_disabled = acdc_app.attempt_serial_number_change("SN54321")
        error_msg = acdc_app.check_for_error_message()
        # Assert serial field is disabled or error message is shown
        assert is_disabled or (error_msg is not None and "not allowed" in error_msg.lower())

    def test_tc_002_remove_rm_dependency_serial_change(self, acdc_app):
        """
        TC-002: Remove RM Dependency for Serial Number Change Restriction
        """
        acdc_app.navigate_to_device_management()
        acdc_app.search_device("SN54321")
        acdc_app.select_device("SN54321")
        acdc_app.open_edit_device_dialog()
        is_disabled = acdc_app.attempt_serial_number_change("SN12345")
        error_msg = acdc_app.check_for_error_message()
        assert is_disabled or (error_msg is not None and "not allowed" in error_msg.lower())

    def test_tc_003_remove_all_rm_dependencies(self, acdc_app):
        """
        TC-003: Remove All RM Dependencies in Device Management
        """
        acdc_app.navigate_to_device_management()
        # Assume multiple devices are listed
        # For each device, check RM status field is not blocking any action
        for serial in ["SN12345", "SN54321", "SN33333"]:
            acdc_app.search_device(serial)
            acdc_app.select_device(serial)
            acdc_app.open_edit_device_dialog()
            # Attempt actions (edit, delete, add) without RM dependency
            is_disabled = acdc_app.attempt_serial_number_change("SN00000")
            assert is_disabled or acdc_app.check_for_error_message() is not None

    def test_tc_004_delete_and_readd_device(self, acdc_app):
        """
        TC-004: Delete Device and Re-add with Corrected Information
        """
        acdc_app.navigate_to_device_management()
        deleted = acdc_app.delete_device("SN99999")
        assert deleted
        device_data = {"name": "Corrected Device", "serial": "SN88888", "model": "ModelX"}
        added = acdc_app.add_device(device_data)
        assert added

    def test_tc_005_attempt_serial_change_api(self):
        """
        TC-005: Attempt to Change Serial Number via API
        """
        api_url = os.getenv("ACDC_API_URL", "https://api.acdc-system.example.com")
        device = get_device_by_serial_api(api_url, "SN12345")
        assert device is not None
        response = attempt_serial_number_change_api(api_url, device["id"], "SN54321")
        # Assert API response indicates failure/restriction
        assert response.status_code != 200 or "error" in response.text.lower()
        # Confirm serial remains unchanged
        device_after = get_device_by_serial_api(api_url, "SN12345")
        assert device_after is not None

    def test_tc_006_system_message_on_serial_change_attempt(self, acdc_app):
        """
        TC-006: System Message on Serial Number Change Attempt
        """
        acdc_app.navigate_to_device_management()
        acdc_app.search_device("SN11111")
        acdc_app.select_device("SN11111")
        acdc_app.open_edit_device_dialog()
        acdc_app.attempt_serial_number_change("SN22222")
        error_msg = acdc_app.check_for_error_message()
        assert error_msg is not None
        assert "not allowed" in error_msg.lower() or "delete and re-add" in error_msg.lower()

    def test_tc_007_reuse_serial_after_deletion(self, acdc_app):
        """
        TC-007: Negative Test - Attempt to Change Serial Number After Device Deletion
        """
        acdc_app.navigate_to_device_management()
        deleted = acdc_app.delete_device("SN22222")
        assert deleted
        device_data = {"name": "Reused Serial Device", "serial": "SN22222", "model": "ModelY"}
        added = acdc_app.add_device(device_data)
        assert added

    def test_tc_008_edge_case_no_rm_status(self, acdc_app):
        """
        TC-008: Edge Case - Attempt to Change Serial Number for Device with No RM Status
        """
        acdc_app.navigate_to_device_management()
        acdc_app.search_device("SN33333")
        acdc_app.select_device("SN33333")
        acdc_app.open_edit_device_dialog()
        is_disabled = acdc_app.attempt_serial_number_change("SN44444")
        error_msg = acdc_app.check_for_error_message()
        assert is_disabled or (error_msg is not None and "not allowed" in error_msg.lower())

    def test_tc_009_audit_log_serial_change_attempt(self):
        """
        TC-009: Audit Log for Serial Number Change Attempts
        """
        api_url = os.getenv("ACDC_API_URL", "https://api.acdc-system.example.com")
        # Attempt serial change via API
        device = get_device_by_serial_api(api_url, "SN44444")
        assert device is not None
        attempt_serial_number_change_api(api_url, device["id"], "SN55555")
        # Check audit log for entry
        logs = get_audit_log_api(api_url, "SN44444")
        assert any("serial number change" in json.dumps(log).lower() for log in logs)

    def test_tc_010_ui_validation_serial_field(self, acdc_app):
        """
        TC-010: UI Validation for Serial Number Field
        """
        acdc_app.navigate_to_device_management()
        acdc_app.search_device("SN55555")
        acdc_app.select_device("SN55555")
        acdc_app.open_edit_device_dialog()
        readonly = acdc_app.check_serial_field_readonly()
        assert readonly

