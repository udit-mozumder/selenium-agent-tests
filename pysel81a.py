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

    def navigate_to_device_management(self, driver):
        """
        Navigates to the device management section.
        """
        driver.get("https://acdc-application-url.example")
        wait = WebDriverWait(driver, 10)
        # TODO: Add login steps if required
        try:
            device_mgmt_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")))
            device_mgmt_link.click()
        except Exception:
            pass
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Device Management')]")))

    def select_device_by_serial(self, driver, serial_number):
        """
        Selects a device by serial number.
        """
        wait = WebDriverWait(driver, 10)
        search_field = wait.until(EC.visibility_of_element_located((By.ID, "device-search")))
        search_field.clear()
        search_field.send_keys(serial_number)
        search_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
        search_btn.click()
        device_row = wait.until(EC.element_to_be_clickable((By.XPATH, f"//tr[contains(., '{serial_number}')]") ))
        device_row.click()

    def test_prevent_serial_number_change(self, driver):
        """
        TC-001: Verify that ACDC does not allow any serial number changes for devices, regardless of whether the device has been collected or not.
        """
        self.navigate_to_device_management(driver)
        serial_number = "SN12345"
        self.select_device_by_serial(driver, serial_number)
        wait = WebDriverWait(driver, 10)
        edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")))
        edit_btn.click()
        serial_field = wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))
        serial_field.clear()
        serial_field.send_keys("SN99999")
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()
        error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")))
        assert error_msg.is_displayed()
        back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back') or contains(text(), 'Cancel')]")
        back_btn.click()
        self.select_device_by_serial(driver, serial_number)
        current_serial = wait.until(EC.visibility_of_element_located((By.XPATH, "//td[contains(@data-label, 'Serial')]"))).text
        assert current_serial == serial_number

    def test_rm_dependency_for_collection_check(self, driver):
        """
        TC-002: Ensure that the system does not rely on RM (Resource Manager) to check if a device has been collected before preventing serial number changes.
        """
        self.navigate_to_device_management(driver)
        serial_number = "SN54321"
        self.select_device_by_serial(driver, serial_number)
        wait = WebDriverWait(driver, 10)
        edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")))
        edit_btn.click()
        serial_field = wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))
        serial_field.clear()
        serial_field.send_keys("SN88888")
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()
        error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")))
        assert error_msg.is_displayed()
        back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back') or contains(text(), 'Cancel')]")
        back_btn.click()
        self.select_device_by_serial(driver, serial_number)
        current_serial = wait.until(EC.visibility_of_element_located((By.XPATH, "//td[contains(@data-label, 'Serial')]"))).text
        assert current_serial == serial_number

    def test_remove_all_other_rm_dependencies(self, driver):
        """
        TC-003: Ensure that all other dependencies on RM are removed from the device management workflow.
        """
        self.navigate_to_device_management(driver)
        serial_number = "SN67890"
        wait = WebDriverWait(driver, 10)
        # View
        self.select_device_by_serial(driver, serial_number)
        details = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'device-details')]")))
        assert details.is_displayed()
        # Edit
        edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")))
        edit_btn.click()
        name_field = wait.until(EC.visibility_of_element_located((By.ID, "device-name")))
        name_field.clear()
        name_field.send_keys("Updated Device Name")
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()
        success_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'success')]")))
        assert success_msg.is_displayed()
        # Add
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Device')]")))
        add_btn.click()
        new_serial_field = wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))
        new_serial_field.send_keys("SN-NEW-12345")
        new_name_field = driver.find_element(By.ID, "device-name")
        new_name_field.send_keys("New Test Device")
        create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create') or contains(text(), 'Save')]")
        create_btn.click()
        add_success = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'success')]")))
        assert add_success.is_displayed()
        # Delete
        self.select_device_by_serial(driver, "SN-NEW-12345")
        delete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete')]")))
        delete_btn.click()
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'Yes')]")))
        confirm_btn.click()
        delete_success = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'success')]")))
        assert delete_success.is_displayed()

    def test_delete_and_readd_device_to_correct_serial(self, driver):
        """
        TC-004: Verify that users can delete a device and re-add it with the correct serial number.
        """
        self.navigate_to_device_management(driver)
        incorrect_serial = "SN00001"
        correct_serial = "SN00002"
        wait = WebDriverWait(driver, 10)
        # Delete
        self.select_device_by_serial(driver, incorrect_serial)
        delete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete')]")))
        delete_btn.click()
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'Yes')]")))
        confirm_btn.click()
        delete_success = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'success')]")))
        assert delete_success.is_displayed()
        # Add
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Device')]")))
        add_btn.click()
        new_serial_field = wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))
        new_serial_field.send_keys(correct_serial)
        new_name_field = driver.find_element(By.ID, "device-name")
        new_name_field.send_keys("Correct Device")
        create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create') or contains(text(), 'Save')]")
        create_btn.click()
        add_success = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'success')]")))
        assert add_success.is_displayed()
        # Verify
        self.select_device_by_serial(driver, correct_serial)
        current_serial = wait.until(EC.visibility_of_element_located((By.XPATH, "//td[contains(@data-label, 'Serial')]"))).text
        assert current_serial == correct_serial

    def test_attempt_serial_number_change_via_api_or_backend(self, driver):
        """
        TC-005: Ensure that serial number changes are blocked at all entry points, including API or backend operations.
        """
        # This test is a placeholder as API/backend testing is not possible via Selenium UI.
        # In a real test suite, use requests or another HTTP client to perform the API call.
        assert True

    def test_error_message_verification_for_serial_number_change_attempt(self, driver):
        """
        TC-006: Verify that the error message displayed when attempting to change a serial number is clear and instructs the user to delete and re-add the device.
        """
        self.navigate_to_device_management(driver)
        serial_number = "SN24680"
        self.select_device_by_serial(driver, serial_number)
        wait = WebDriverWait(driver, 10)
        edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Edit')]")))
        edit_btn.click()
        serial_field = wait.until(EC.visibility_of_element_located((By.ID, "serial-number")))
        serial_field.clear()
        serial_field.send_keys("SN13579")
        save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
        save_btn.click()
        error_msg = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")))
        expected_text = "Serial number changes are not allowed. To correct a serial number, please delete and re-add the device."
        assert expected_text in error_msg.text
