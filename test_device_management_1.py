import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

@pytest.fixture(scope="class")
def setup(request):
    # Setup WebDriver
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get("https://acdc.example.com/login")
    
    # Login to the application
    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")
    
    username.send_keys("admin")
    password.send_keys("admin123")
    login_button.click()
    
    # Wait for dashboard to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dashboard"))
    )
    
    # Navigate to Device Management
    nav_menu = driver.find_element(By.ID, "nav-menu")
    nav_menu.click()
    
    device_mgmt = driver.find_element(By.ID, "device-management")
    device_mgmt.click()
    
    # Wait for device management page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "device-list"))
    )
    
    request.cls.driver = driver
    
    yield
    
    # Teardown
    driver.quit()

@pytest.mark.usefixtures("setup")
class TestDeviceManagement:
    
    def test_tc001_view_device_list(self):
        """TC-001: Verify user can view the list of devices"""
        device_list = self.driver.find_element(By.ID, "device-list")
        assert device_list.is_displayed(), "Device list is not displayed"
        
        # Verify column headers
        headers = self.driver.find_elements(By.CSS_SELECTOR, "#device-list th")
        expected_headers = ["Device ID", "Name", "Type", "Status", "Last Connected", "Actions"]
        actual_headers = [header.text for header in headers]
        
        assert actual_headers == expected_headers, f"Expected headers {expected_headers}, got {actual_headers}"
        
        # Verify at least one device is listed
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        assert len(devices) > 0, "No devices are listed in the table"
    
    def test_tc002_search_device(self):
        """TC-002: Verify user can search for a device"""
        search_box = self.driver.find_element(By.ID, "device-search")
        search_box.clear()
        search_box.send_keys("Test Device 1")
        
        search_button = self.driver.find_element(By.ID, "search-button")
        search_button.click()
        
        # Wait for search results
        time.sleep(2)
        
        # Verify search results
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        assert len(devices) > 0, "No devices found in search results"
        
        device_name = devices[0].find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        assert "Test Device 1" in device_name, f"Expected 'Test Device 1' in device name, got {device_name}"
    
    def test_tc003_filter_devices(self):
        """TC-003: Verify user can filter devices by status"""
        status_filter = self.driver.find_element(By.ID, "status-filter")
        status_filter.click()
        
        # Select 'Active' status
        active_option = self.driver.find_element(By.CSS_SELECTOR, "#status-dropdown option[value='active']")
        active_option.click()
        
        apply_filter = self.driver.find_element(By.ID, "apply-filter")
        apply_filter.click()
        
        # Wait for filter to apply
        time.sleep(2)
        
        # Verify all displayed devices have 'Active' status
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        for device in devices:
            status = device.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            assert status == "Active", f"Expected status 'Active', got {status}"
    
    def test_tc004_add_new_device(self):
        """TC-004: Verify user can add a new device"""
        add_device_button = self.driver.find_element(By.ID, "add-device-button")
        add_device_button.click()
        
        # Wait for add device form to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-device-form"))
        )
        
        # Fill in device details
        device_name = self.driver.find_element(By.ID, "device-name")
        device_type = self.driver.find_element(By.ID, "device-type")
        device_id = self.driver.find_element(By.ID, "device-id")
        
        device_name.send_keys("Automated Test Device")
        device_type.send_keys("Sensor")
        device_id.send_keys("AUTO-123")
        
        # Submit form
        submit_button = self.driver.find_element(By.ID, "submit-device")
        submit_button.click()
        
        # Wait for success message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        
        success_message = self.driver.find_element(By.CLASS_NAME, "success-message").text
        assert "Device added successfully" in success_message, f"Expected success message, got {success_message}"
        
        # Verify device appears in the list
        self.driver.find_element(By.ID, "device-search").clear()
        self.driver.find_element(By.ID, "device-search").send_keys("Automated Test Device")
        self.driver.find_element(By.ID, "search-button").click()
        
        time.sleep(2)
        
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        assert len(devices) > 0, "Newly added device not found in list"
    
    def test_tc005_edit_device(self):
        """TC-005: Verify user can edit a device"""
        # Search for the device to edit
        self.driver.find_element(By.ID, "device-search").clear()
        self.driver.find_element(By.ID, "device-search").send_keys("Automated Test Device")
        self.driver.find_element(By.ID, "search-button").click()
        
        time.sleep(2)
        
        # Click edit button for the first device
        edit_button = self.driver.find_element(By.CSS_SELECTOR, ".edit-device-button")
        edit_button.click()
        
        # Wait for edit form to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "edit-device-form"))
        )
        
        # Update device name
        device_name = self.driver.find_element(By.ID, "device-name")
        device_name.clear()
        device_name.send_keys("Updated Test Device")
        
        # Submit form
        submit_button = self.driver.find_element(By.ID, "submit-device-edit")
        submit_button.click()
        
        # Wait for success message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        
        success_message = self.driver.find_element(By.CLASS_NAME, "success-message").text
        assert "Device updated successfully" in success_message, f"Expected success message, got {success_message}"
        
        # Verify device name was updated
        self.driver.find_element(By.ID, "device-search").clear()
        self.driver.find_element(By.ID, "device-search").send_keys("Updated Test Device")
        self.driver.find_element(By.ID, "search-button").click()
        
        time.sleep(2)
        
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        assert len(devices) > 0, "Updated device not found in list"
        
        device_name = devices[0].find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        assert device_name == "Updated Test Device", f"Expected 'Updated Test Device', got {device_name}"
    
    def test_tc006_delete_device(self):
        """TC-006: Verify user can delete a device"""
        # Search for the device to delete
        self.driver.find_element(By.ID, "device-search").clear()
        self.driver.find_element(By.ID, "device-search").send_keys("Updated Test Device")
        self.driver.find_element(By.ID, "search-button").click()
        
        time.sleep(2)
        
        # Get initial count of devices
        initial_devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        initial_count = len(initial_devices)
        
        # Click delete button for the first device
        delete_button = self.driver.find_element(By.CSS_SELECTOR, ".delete-device-button")
        delete_button.click()
        
        # Wait for confirmation dialog
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "confirm-delete"))
        )
        
        # Confirm deletion
        confirm_button = self.driver.find_element(By.ID, "confirm-delete")
        confirm_button.click()
        
        # Wait for success message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        
        success_message = self.driver.find_element(By.CLASS_NAME, "success-message").text
        assert "Device deleted successfully" in success_message, f"Expected success message, got {success_message}"
        
        # Verify device was deleted
        self.driver.find_element(By.ID, "device-search").clear()
        self.driver.find_element(By.ID, "device-search").send_keys("Updated Test Device")
        self.driver.find_element(By.ID, "search-button").click()
        
        time.sleep(2)
        
        devices = self.driver.find_elements(By.CSS_SELECTOR, "#device-list tbody tr")
        assert len(devices) == 0, "Device was not deleted successfully"
    
    def test_tc007_bulk_device_import(self):
        """TC-007: Verify user can import devices in bulk"""
        import_button = self.driver.find_element(By.ID, "import-devices-button")
        import_button.click()
        
        # Wait for import form to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "import-devices-form"))
        )
        
        # Upload file (simulated)
        file_input = self.driver.find_element(By.ID, "device-csv-file")
        file_input.send_keys("/path/to/test/devices.csv")
        
        # Submit form
        submit_button = self.driver.find_element(By.ID, "submit-import")
        submit_button.click()
        
        # Wait for success message
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )