
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

pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

class DeviceManagementTests:
    """
    Test suite for device management scenarios focusing on serial number restrictions
    and RM dependency removal.
    """

    @pytest.fixture
    def driver(self):
        """
        Setup fixture to initialize and configure the WebDriver.
        Returns a configured Chrome WebDriver and handles cleanup.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(driver, 20)
        yield driver
        driver.quit()

    def capture_screenshot(self, driver, test_name):
        """
        Captures a screenshot when a test fails.
        """
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/{test_name}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)

    def navigate_to_device_management(self, driver):
        """
        Navigates to the device management section of the application.
        """
        base_url = os.getenv("APP_URL", "https://example.com")
        driver.get(base_url)
        try:
            # Log in if needed (assuming login is required)
            if "login" in driver.current_url.lower():
                username = os.getenv("APP_USERNAME", "admin")
                password = os.getenv("APP_PASSWORD", "admin")
                username_field = self.wait.until(
                    EC.visibility_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(username)
                password_field = self.wait.until(
                    EC.visibility_of_element_located((By.NAME, "password"))
                )
                password_field.clear()
                password_field.send_keys(password)
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]")
                )
                login_button.click()
            # Navigate to device management section
            device_management_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Device Management')]")
            )
            device_management_link.click()
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Device Management')]")
            )
        except Exception as e:
            self.capture_screenshot(driver, "navigation_failure")
            raise Exception(f"Failed to navigate to device management: {str(e)}")

    def select_device(self, driver, device_index=0):
        """
        Selects a device from the device list.
        """
        try:
            device_list = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//table//tr[contains(@class, 'device-row')]")
            )
            assert len(device_list) > 0, "No devices found in the list"
            if device_index < len(device_list):
                device = device_list[device_index]
                device.find_element(By.XPATH, ".//button[contains(text(), 'Edit') or contains(@class, 'edit')]").click()
                return device
            else:
                raise Exception(f"Device index {device_index} is out of range. Only {len(device_list)} devices found.")
        except Exception as e:
            self.capture_screenshot(driver, "device_selection_failure")
            raise Exception(f"Failed to select device: {str(e)}")

    def test_prevent_serial_number_change(self, driver):
        """
        TC-001: Verify that the system does not allow changing the serial number for any device,
        regardless of collection status.
        """
        try:
            self.navigate_to_device_management(driver)
            self.select_device(driver)
            edit_form = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//form[contains(@class, 'device-form')]")
            )
            serial_number_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='serialNumber' or @id='serialNumber']"))
            )
            is_disabled = serial_number_field.get_attribute("disabled") == "true" or serial_number_field.get_attribute("readonly") == "true"
            if not is_disabled:
                original_value = serial_number_field.get_attribute("value")
                serial_number_field.clear()
                serial_number_field.send_keys("NEW-SERIAL-123")
                save_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or contains(@class, 'save')]")
                )
                save_button.click()
                error_message = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
                )
                assert "serial number" in error_message.text.lower(), "Error message does not mention serial number"
                updated_value = serial_number_field.get_attribute("value")
                assert updated_value == original_value, "Serial number was changed despite restrictions"
            assert is_disabled or "error_message" in locals(), "Serial number field should be disabled or show error on save"
        except Exception as e:
            self.capture_screenshot(driver, "test_prevent_serial_number_change_failure")
            raise Exception(f"Test failed: {str(e)}")

    def test_remove_rm_dependency_for_serial_number(self, driver):
        """
        TC-002: Ensure that the system does not rely on RM (Resource Management) to check for
        device collection status when editing serial numbers.
        """
        try:
            self.navigate_to_device_management(driver)
            self.select_device(driver)
            page_source = driver.page_source.lower()
            rm_references = [
                "resourcemanagement",
                "rm-api",
                "rm_status",
                "collection_status",
                "rm.check",
                "rm-dependency"
            ]
            rm_references_found = [ref for ref in rm_references if ref in page_source]
            serial_number_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='serialNumber' or @id='serialNumber']"))
            )
            is_disabled = serial_number_field.get_attribute("disabled") == "true" or serial_number_field.get_attribute("readonly") == "true"
            assert is_disabled, "Serial number field should be disabled regardless of RM status"
            assert len(rm_references_found) == 0, f"RM dependencies found: {rm_references_found}"
        except Exception as e:
            self.capture_screenshot(driver, "test_remove_rm_dependency_failure")
            raise Exception(f"Test failed: {str(e)}")

    def test_remove_all_rm_dependencies(self, driver):
        """
        TC-003: Verify that all other dependencies on RM within device management are removed.
        """
        try:
            self.navigate_to_device_management(driver)
            device_list_page = driver.page_source.lower()
            rm_references_list = ["resourcemanagement", "rm-api", "rm_status", "collection_status"]
            rm_refs_in_list = [ref for ref in rm_references_list if ref in device_list_page]
            self.select_device(driver)
            edit_form_page = driver.page_source.lower()
            rm_refs_in_edit = [ref for ref in rm_references_list if ref in edit_form_page]
            name_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='deviceName' or @id='deviceName']"))
            )
            original_name = name_field.get_attribute("value")
            name_field.clear()
            name_field.send_keys(f"{original_name}_edited")
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or contains(@class, 'save')]")
            )
            save_button.click()
            self.wait.until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'loading')]")
            )
            post_save_page = driver.page_source.lower()
            rm_refs_post_save = [ref for ref in rm_references_list if ref in post_save_page]
            assert not rm_refs_in_list, f"RM dependencies found in list: {rm_refs_in_list}"
            assert not rm_refs_in_edit, f"RM dependencies found in edit: {rm_refs_in_edit}"
            assert not rm_refs_post_save, f"RM dependencies found after save: {rm_refs_post_save}"
        except Exception as e:
            self.capture_screenshot(driver, "test_remove_all_rm_dependencies_failure")
            raise Exception(f"Test failed: {str(e)}")

    def test_delete_and_readd_device_with_correct_serial(self, driver):
        """
        TC-004: Verify that a user can delete a device and re-add it with the correct serial number as an alternative to editing.
        """
        try:
            self.navigate_to_device_management(driver)
            self.select_device(driver)
            delete_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Delete') or contains(@class, 'delete')]")
            )
            delete_button.click()
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm') or contains(@class, 'confirm')]")
            )
            confirm_button.click()
            self.wait.until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'device-row')]")
            )
            add_device_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Device') or contains(@class, 'add-device')]")
            )
            add_device_button.click()
            serial_field = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@name='serialNumber' or @id='serialNumber']"))
            )
            serial_field.send_keys("CORRECTED-SERIAL-123")
            name_field = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, "//input[@name='deviceName' or @id='deviceName']"))
            )
            name_field.send_keys("Re-added Device")
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or contains(@class, 'save')]")
            )
            save_button.click()
            device_row = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'CORRECTED-SERIAL-123')]")
            )
            assert device_row.is_displayed(), "Re-added device with corrected serial number not found"
        except Exception as e:
            self.capture_screenshot(driver, "test_delete_and_readd_device_failure")
            raise Exception(f"Test failed: {str(e)}")

    def test_edit_other_device_fields(self, driver):
        """
        TC-005: Ensure that fields other than serial number can still be edited as expected.
        """
        try:
            self.navigate_to_device_management(driver)
            self.select_device(driver)
            name_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='deviceName' or @id='deviceName']"))
            )
            original_name = name_field.get_attribute("value")
            new_name = f"{original_name}_updated"
            name_field.clear()
            name_field.send_keys(new_name)
            save_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or contains(@class, 'save')]")
            )
            save_button.click()
            self.wait.until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'loading')]")
            )
            device_name_cell = self.wait.until(
                EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{new_name}')]")
            )
            assert device_name_cell.is_displayed(), "Device name was not updated"
            serial_number_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='serialNumber' or @id='serialNumber']"))
            )
            is_disabled = serial_number_field.get_attribute("disabled") == "true" or serial_number_field.get_attribute("readonly") == "true"
            assert is_disabled, "Serial number field should remain uneditable"
        except Exception as e:
            self.capture_screenshot(driver, "test_edit_other_device_fields_failure")
            raise Exception(f"Test failed: {str(e)}")

    def test_serial_number_edit_ui_feedback(self, driver):
        """
        TC-006: Verify that the UI provides clear feedback (e.g., disabled field, tooltip, or error message)
        when a user attempts to edit the serial number.
        """
        try:
            self.navigate_to_device_management(driver)
            self.select_device(driver)
            serial_number_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='serialNumber' or @id='serialNumber']"))
            )
            is_disabled = serial_number_field.get_attribute("disabled") == "true" or serial_number_field.get_attribute("readonly") == "true"
            tooltip = serial_number_field.get_attribute("title")
            if not is_disabled:
                serial_number_field.clear()
                serial_number_field.send_keys("TRY-EDIT-SERIAL")
                save_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or contains(@class, 'save')]")
                )
                save_button.click()
                error_message = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
                )
                assert "serial number" in error_message.text.lower(), "No error message for serial number edit"
            assert is_disabled or tooltip or "error_message" in locals(), "No UI feedback for serial number edit"
        except Exception as e:
            self.capture_screenshot(driver, "test_serial_number_edit_ui_feedback_failure")
            raise Exception(f"Test failed: {str(e)}")
"