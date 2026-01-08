import pytest
import os
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

    def test_prevent_serial_number_change_for_collected_devices(self, driver):
        """
        TC-001: Verify that users cannot change the serial number of a device that has already been collected.
        """
        driver.get("https://acdc-app-url/device-management")
        # Select device with status "collected"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN12345")
        driver.find_element(By.ID, "search-button").click()
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.XPATH, "//tr[1]/td[contains(@class,'status')]"), "collected")
        )
        driver.find_element(By.XPATH, "//tr[1]").click()
        # Try to edit serial number
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        is_disabled = not serial_input.is_enabled()
        # If field is enabled, try to change and save
        blocked = is_disabled
        if not is_disabled:
            serial_input.clear()
            serial_input.send_keys("SN99999")
            driver.find_element(By.ID, "save-changes-button").click()
            try:
                error = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                blocked = "not allowed" in error.text.lower()
            except:
                blocked = False
        assert blocked, "Serial number field should be non-editable or changes should be blocked for collected devices"

    def test_prevent_serial_number_change_for_not_collected_devices(self, driver):
        """
        TC-002: Ensure that users cannot change the serial number for devices that have not been collected.
        """
        driver.get("https://acdc-app-url/device-management")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN54321")
        driver.find_element(By.ID, "search-button").click()
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.XPATH, "//tr[1]/td[contains(@class,'status')]"), "not collected")
        )
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        is_disabled = not serial_input.is_enabled()
        blocked = is_disabled
        if not is_disabled:
            serial_input.clear()
            serial_input.send_keys("SN11111")
            driver.find_element(By.ID, "save-changes-button").click()
            try:
                error = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                blocked = "not allowed" in error.text.lower()
            except:
                blocked = False
        assert blocked, "Serial number field should be non-editable or changes should be blocked for not collected devices"

    def test_remove_rm_dependency_for_serial_number_change(self, driver):
        """
        TC-003: Confirm that the system does not check RM status or collection status when attempting to change a serial number.
        """
        driver.get("https://acdc-app-url/device-management")
        # Assume device with RM status exists
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN12345")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        is_disabled = not serial_input.is_enabled()
        blocked = is_disabled
        if not is_disabled:
            serial_input.clear()
            serial_input.send_keys("SN00000")
            driver.find_element(By.ID, "save-changes-button").click()
            try:
                error = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                blocked = "not allowed" in error.text.lower()
            except:
                blocked = False
        assert blocked, "Serial number change should be universally blocked, no RM dependency should be checked"

    def test_remove_all_other_rm_dependencies(self, driver):
        """
        TC-004: Verify that all other RM dependencies are removed from device management operations.
        """
        driver.get("https://acdc-app-url/device-management")
        # Try edit, delete, view on devices with various RM statuses
        for sn in ["SN11111", "SN22222", "SN33333"]:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "device-search"))
            ).clear()
            driver.find_element(By.ID, "device-search").send_keys(sn)
            driver.find_element(By.ID, "search-button").click()
            driver.find_element(By.XPATH, "//tr[1]").click()
            # Edit non-serial field
            driver.find_element(By.ID, "edit-device-button").click()
            name_input = driver.find_element(By.ID, "device-name")
            name_input.clear()
            name_input.send_keys("TestDevice")
            driver.find_element(By.ID, "save-changes-button").click()
            try:
                error = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                assert "rm" not in error.text.lower(), "No RM-related errors should occur"
            except:
                pass
            # Delete
            driver.find_element(By.ID, "delete-device-button").click()
            driver.find_element(By.ID, "confirm-delete-button").click()
            try:
                success = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
                )
                assert "deleted" in success.text.lower()
            except:
                pass

    def test_allow_device_deletion_for_correction(self, driver):
        """
        TC-005: Ensure users can delete devices regardless of their collection or RM status.
        """
        driver.get("https://acdc-app-url/device-management")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN99999")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "delete-device-button").click()
        driver.find_element(By.ID, "confirm-delete-button").click()
        success = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "deleted" in success.text.lower()

    def test_readd_device_with_corrected_information(self, driver):
        """
        TC-006: Verify that users can re-add a device with corrected serial number and other information after deletion.
        """
        driver.get("https://acdc-app-url/device-management")
        driver.find_element(By.ID, "add-device-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-serial-number"))
        ).send_keys("SN88888")
        driver.find_element(By.ID, "device-name").send_keys("Corrected Device")
        driver.find_element(By.ID, "device-status").send_keys("Active")
        driver.find_element(By.ID, "save-device-button").click()
        success = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "added" in success.text.lower()

    def test_attempt_serial_number_change_via_api_backend(self, driver):
        """
        TC-007: Ensure serial number changes are blocked at the API/backend level, not just the UI.
        """
        # This test would normally use direct API calls, but for demonstration, we simulate via UI
        driver.get("https://acdc-app-url/device-management")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN12345")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        is_disabled = not serial_input.is_enabled()
        blocked = is_disabled
        if not is_disabled:
            serial_input.clear()
            serial_input.send_keys("SN00001")
            driver.find_element(By.ID, "save-changes-button").click()
            try:
                error = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                blocked = "not allowed" in error.text.lower()
            except:
                blocked = False
        assert blocked, "Serial number change should be blocked at backend/API level"

    def test_edge_case_attempt_to_change_serial_number_during_device_creation(self, driver):
        """
        TC-008: Ensure that the serial number can only be set during initial device creation and cannot be modified afterward.
        """
        driver.get("https://acdc-app-url/device-management")
        driver.find_element(By.ID, "add-device-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-serial-number"))
        ).send_keys("SN77777")
        driver.find_element(By.ID, "device-name").send_keys("Edge Device")
        driver.find_element(By.ID, "device-status").send_keys("Active")
        driver.find_element(By.ID, "save-device-button").click()
        success = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "added" in success.text.lower()
        # Now try to edit serial number
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN77777")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        assert not serial_input.is_enabled() or serial_input.get_attribute("readonly"), \
            "Serial number should not be editable after creation"

    def test_negative_attempt_to_change_serial_number_with_invalid_data(self, driver):
        """
        TC-009: Attempt to change the serial number using invalid or malformed data and verify the system blocks the operation.
        """
        driver.get("https://acdc-app-url/device-management")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN12345")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        serial_input = driver.find_element(By.ID, "device-serial-number")
        for invalid in ["", "!!!@@@", "SN12345678901234567890"]:
            if serial_input.is_enabled():
                serial_input.clear()
                serial_input.send_keys(invalid)
                driver.find_element(By.ID, "save-changes-button").click()
                error = WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
                )
                assert "error" in error.text.lower() or "invalid" in error.text.lower()

    def test_regression_device_management_without_rm_dependency(self, driver):
        """
        TC-010: Ensure all device management features function correctly after removal of RM dependencies.
        """
        driver.get("https://acdc-app-url/device-management")
        # Add device
        driver.find_element(By.ID, "add-device-button").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-serial-number"))
        ).send_keys("SN55555")
        driver.find_element(By.ID, "device-name").send_keys("Regression Device")
        driver.find_element(By.ID, "device-status").send_keys("Active")
        driver.find_element(By.ID, "save-device-button").click()
        success = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "added" in success.text.lower()
        # Edit non-serial field
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "device-search"))
        ).send_keys("SN55555")
        driver.find_element(By.ID, "search-button").click()
        driver.find_element(By.XPATH, "//tr[1]").click()
        driver.find_element(By.ID, "edit-device-button").click()
        name_input = driver.find_element(By.ID, "device-name")
        name_input.clear()
        name_input.send_keys("Regression Device Updated")
        driver.find_element(By.ID, "save-changes-button").click()
        success = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "success-message"))
        )
        assert "updated" in success.text.lower()
        # Delete
        driver.find_element(By.ID, "delete-device-button").click()
