"""
import pytest

pytestmark = pytest.mark.skip(
    reason="Agent-generated E2E test requires real application UI; skipped in CI"
)

# ---------------------------------------------------------------------------
# Import necessary modules
# ---------------------------------------------------------------------------
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Configuration Section
# ---------------------------------------------------------------------------
# Base URL for the API documentation or Swagger UI (replace with actual URL)
API_DOC_URL = os.getenv("DISCOUNT_API_DOC_URL", "https://example.com/api-docs")

# JWT Token for Authorization (replace with actual token or fetch dynamically)
VALID_JWT_TOKEN = os.getenv("DISCOUNT_API_JWT", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
INVALID_JWT_TOKEN = "Bearer invalidtoken"

# ---------------------------------------------------------------------------
# Helper Functions for API Testing via Swagger UI
# ---------------------------------------------------------------------------
class DiscountApiUiHelper:
    """
    Helper class to interact with the API documentation UI (e.g., Swagger UI)
    and perform GET requests to /api/v1/discounts endpoint using Selenium.
    """

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def open_api_docs(self):
        """
        Navigate to the API documentation page.
        """
        self.driver.get(API_DOC_URL)
        time.sleep(2)  # Wait for page to load

    def authorize(self, jwt_token: str):
        """
        Authorize using the JWT token in Swagger UI.
        """
        # Locate the "Authorize" button and click it
        authorize_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Authorize')]"))
        )
        authorize_btn.click()
        time.sleep(1)

        # Find the input field for JWT token (adjust selector as needed)
        token_input = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@type='text' and contains(@placeholder, 'Bearer')]"))
        )
        token_input.clear()
        token_input.send_keys(jwt_token)

        # Click the "Authorize" button in the modal
        modal_authorize_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Authorize') and @type='submit']"))
        )
        modal_authorize_btn.click()
        time.sleep(1)

        # Close the modal
        close_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Close')]"))
        )
        close_btn.click()
        time.sleep(1)

    def expand_endpoint(self, endpoint: str):
        """
        Expand the GET /api/v1/discounts endpoint in Swagger UI.
        """
        # Locate the endpoint section by its summary text
        endpoint_section = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//section[contains(.,'{endpoint}')]"))
        )
        endpoint_section.click()
        time.sleep(1)

    def set_query_parameters(self, params: Dict[str, str]):
        """
        Set query parameters in the UI for the endpoint.
        """
        for key, value in params.items():
            param_input = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, f"//input[@placeholder='{key}']"))
            )
            param_input.clear()
            param_input.send_keys(value)
            time.sleep(0.5)

    def execute_request(self):
        """
        Click the "Execute" button to send the API request.
        """
        execute_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Execute')]"))
        )
        execute_btn.click()
        time.sleep(2)  # Wait for response

    def get_response_status_code(self) -> int:
        """
        Retrieve the HTTP status code from the response section.
        """
        status_code_elem = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, "//td[@class='response-col_status']"))
        )
        return int(status_code_elem.text.strip())

    def get_response_body(self) -> Any:
        """
        Retrieve and parse the JSON response body.
        """
        response_elem = self.wait.until(
            EC.visibility_of_element_located((By.XPATH, "//pre[@class='microlight']"))
        )
        response_text = response_elem.text.strip()
        try:
            return json.loads(response_text)
        except Exception:
            return response_text

    def clear_authorization(self):
        """
        Clear the authorization from Swagger UI.
        """
        # Click "Authorize" again
        authorize_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Authorize')]"))
        )
        authorize_btn.click()
        time.sleep(1)
        # Click "Logout" in the modal
        logout_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Logout')]"))
        )
        logout_btn.click()
        time.sleep(1)
        # Close modal
        close_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Close')]"))
        )
        close_btn.click()
        time.sleep(1)

# ---------------------------------------------------------------------------
# Discount Entity Validation Functions
# ---------------------------------------------------------------------------
def validate_discount_entity(discount: Dict[str, Any], all_discounts: List[Dict[str, Any]], market_uniqueness: Dict[str, set]) -> List[str]:
    """
    Validate a single discount entity against business rules.
    Returns a list of validation error messages (empty if valid).
    """
    errors = []

    # a. Required fields
    required_fields = ["name", "identifier", "market", "start_date", "end_date"]
    for field in required_fields:
        if field not in discount:
            errors.append(f"Missing required field: {field}")

    # b. discount_type validation
    allowed_types = ["product_only", "service_only", "product_and_service"]
    if "discount_type" in discount and discount["discount_type"] not in allowed_types:
        errors.append(f"Invalid discount_type: {discount.get('discount_type')}")

    # c. applicable_globally is boolean
    if "applicable_globally" in discount and not isinstance(discount["applicable_globally"], bool):
        errors.append("applicable_globally is not boolean")

    # d. inactive is boolean
    if "inactive" in discount and not isinstance(discount["inactive"], bool):
        errors.append("inactive is not boolean")

    # e. identifier format
    if "identifier" in discount:
        if not isinstance(discount["identifier"], str) or not discount["identifier"].isalnum():
            errors.append(f"Identifier format invalid: {discount['identifier']}")

    # f. name and identifier uniqueness within market
    market = discount.get("market")
    if market:
        if market not in market_uniqueness:
            market_uniqueness[market] = set()
        key = (discount.get("name"), discount.get("identifier"))
        if key in market_uniqueness[market]:
            errors.append(f"Duplicate name/identifier in market {market}: {key}")
        else:
            market_uniqueness[market].add(key)

    # g. start_date < end_date
    try:
        start_date = datetime.fromisoformat(discount["start_date"])
        end_date = datetime.fromisoformat(discount["end_date"])
        if start_date >= end_date:
            errors.append(f"start_date >= end_date: {discount['start_date']} >= {discount['end_date']}")
    except Exception:
        errors.append("Invalid date format in start_date or end_date")

    # h. partners empty when applicable_globally is true
    if discount.get("applicable_globally") is True:
        if "partners" in discount and discount["partners"]:
            errors.append("partners should be empty when applicable_globally is true")
    # i. partners present when applicable_globally is false
    if discount.get("applicable_globally") is False:
        if "partners" not in discount or not discount["partners"]:
            errors.append("partners should be present when applicable_globally is false")

    # j. all plan_benefits plans belong to the same market
    if "plan_benefits" in discount and isinstance(discount["plan_benefits"], list):
        for plan in discount["plan_benefits"]:
            if plan.get("market") and plan.get("market") != market:
                errors.append(f"plan_benefit market mismatch: {plan.get('market')} != {market}")

    return errors

def validate_discount_serialization(discount: Dict[str, Any]) -> List[str]:
    """
    Validate that each discount is serialized with all required fields and nested arrays.
    Returns a list of missing/invalid fields.
    """
    errors = []
    required_fields = [
        "id", "name", "identifier", "eligibility_window_days", "start_date", "end_date",
        "market", "is_default", "discount_type", "environment_flag", "applicable_globally"
    ]
    for field in required_fields:
        if field not in discount:
            errors.append(f"Missing field: {field}")

    # partners is array of strings
    if "partners" in discount and not (isinstance(discount["partners"], list) and all(isinstance(p, str) for p in discount["partners"])):
        errors.append("partners is not array of strings")

    # product_models is array of objects with sku and name
    if "product_models" in discount:
        if not isinstance(discount["product_models"], list):
            errors.append("product_models is not array")
        else:
            for model in discount["product_models"]:
                if not isinstance(model, dict) or "sku" not in model or "name" not in model:
                    errors.append("product_models missing sku or name")

    # plan_benefits is array of objects with unit, value, plan, plan_id, adjustment
    if "plan_benefits" in discount:
        if not isinstance(discount["plan_benefits"], list):
            errors.append("plan_benefits is not array")
        else:
            for benefit in discount["plan_benefits"]:
                for field in ["unit", "value", "plan", "plan_id", "adjustment"]:
                    if field not in benefit:
                        errors.append(f"plan_benefits missing field: {field}")

    return errors

# ---------------------------------------------------------------------------
# Selenium Test Suite for Discount API via Swagger UI
# ---------------------------------------------------------------------------
class TestDiscountApiUi:
    """
    Selenium-based UI automation suite for validating Discount API via Swagger UI.
    Each test corresponds to a test case from the suite.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self):
        """
        Setup Chrome WebDriver with headless mode for tests.
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        helper = DiscountApiUiHelper(driver)
        yield helper
        # Teardown: Quit the driver after tests
        driver.quit()

    # -----------------------------------------------------------------------
    # TC-001: Retrieve Active Discounts Without Filters
    # -----------------------------------------------------------------------
    def test_tc_001_active_discounts(self, setup_class):
        """
        Verify GET /api/v1/discounts returns only active discounts when no filters are applied.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        # No query parameters for this test
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        # Assert HTTP status code is 200
        assert status_code == 200, f"Expected 200, got {status_code}"

        # Assert response is a JSON array
        assert isinstance(response, list), "Response is not a JSON array"

        # Check each discount for active status
        now_utc = datetime.utcnow()
        for discount in response:
            end_date = datetime.fromisoformat(discount["end_date"])
            assert end_date > now_utc, f"Discount expired: {discount['identifier']}"
            assert discount["inactive"] is False, f"Discount inactive: {discount['identifier']}"

    # -----------------------------------------------------------------------
    # TC-002: Retrieve Expired Discounts
    # -----------------------------------------------------------------------
    def test_tc_002_expired_discounts(self, setup_class):
        """
        Verify GET /api/v1/discounts?expired=true returns expired discounts.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"expired": "true"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        # Assert HTTP status code is 200
        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # Should contain both expired and active discounts
        has_expired = any(datetime.fromisoformat(d["end_date"]) < datetime.utcnow() for d in response)
        has_active = any(datetime.fromisoformat(d["end_date"]) > datetime.utcnow() for d in response)
        assert has_expired, "No expired discounts returned"
        assert has_active, "No active discounts returned"

    # -----------------------------------------------------------------------
    # TC-003: Filter Discounts by Market Name
    # -----------------------------------------------------------------------
    def test_tc_003_market_filter(self, setup_class):
        """
        Verify discounts can be filtered by market name.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"market": "US"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # All discounts should have market == "US"
        for discount in response:
            assert discount["market"] == "US", f"Discount market mismatch: {discount['market']}"

    # -----------------------------------------------------------------------
    # TC-004: Filter Discounts by Identifier
    # -----------------------------------------------------------------------
    def test_tc_004_identifier_filter(self, setup_class):
        """
        Verify discounts can be filtered by identifier.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"identifier": "DISC2024"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # All discounts should have identifier == "DISC2024"
        for discount in response:
            assert discount["identifier"] == "DISC2024", f"Discount identifier mismatch: {discount['identifier']}"

    # -----------------------------------------------------------------------
    # TC-005: Filter Discounts by Environment Flag
    # -----------------------------------------------------------------------
    def test_tc_005_environment_flag_filter(self, setup_class):
        """
        Verify discounts can be filtered by environment_flag.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"environment_flag": "true"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # All discounts should have environment_flag == True
        for discount in response:
            assert discount["environment_flag"] is True, f"environment_flag mismatch: {discount['environment_flag']}"

    # -----------------------------------------------------------------------
    # TC-006: Filter Discounts by Product SKU and Market
    # -----------------------------------------------------------------------
    def test_tc_006_productsku_and_market_filter(self, setup_class):
        """
        Verify discounts can be filtered by productSku and market together.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"productSku": "SKU123", "market": "US"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # All discounts should be for SKU123 in US market
        for discount in response:
            assert discount["market"] == "US", f"Discount market mismatch: {discount['market']}"
            # Check if productSku is present in product_models
            found = any(model.get("sku") == "SKU123" for model in discount.get("product_models", []))
            assert found, f"SKU123 not found in product_models for discount {discount['identifier']}"

    # -----------------------------------------------------------------------
    # TC-007: Error When Product SKU Provided Without Market
    # -----------------------------------------------------------------------
    def test_tc_007_productsku_without_market(self, setup_class):
        """
        Verify providing productSku without market returns HTTP 400 and error message.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"productSku": "SKU123"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 400, f"Expected 400, got {status_code}"
        assert "Market is required" in str(response), f"Error message not found: {response}"

    # -----------------------------------------------------------------------
    # TC-008: Error When Authentication Fails
    # -----------------------------------------------------------------------
    def test_tc_008_authentication_fails(self, setup_class):
        """
        Verify request without valid JWT token returns HTTP 401 Unauthorized.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.clear_authorization()  # Remove any valid token
        helper.expand_endpoint("GET /api/v1/discounts")
        # No Authorization header
        helper.execute_request()
        status_code = helper.get_response_status_code()
        assert status_code == 401, f"Expected 401, got {status_code}"

        # Optionally, try with invalid token
        helper.authorize(INVALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.execute_request()
        status_code = helper.get_response_status_code()
        assert status_code == 401, f"Expected 401 with invalid token, got {status_code}"

    # -----------------------------------------------------------------------
    # TC-009: Validate Discount Entity Fields and Business Logic
    # -----------------------------------------------------------------------
    def test_tc_009_discount_entity_validation(self, setup_class):
        """
        Verify all returned discount objects comply with entity validations.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        # Validate each discount object
        market_uniqueness = {}
        for discount in response:
            errors = validate_discount_entity(discount, response, market_uniqueness)
            assert not errors, f"Discount entity validation failed: {errors}"

    # -----------------------------------------------------------------------
    # TC-010: Empty Array When No Discounts Match Filters
    # -----------------------------------------------------------------------
    def test_tc_010_empty_array_no_match(self, setup_class):
        """
        Verify empty array is returned when no discounts match filters.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.set_query_parameters({"market": "NonExistentMarket"})
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"
        assert len(response) == 0, f"Expected empty array, got {len(response)} items"

    # -----------------------------------------------------------------------
    # TC-011: Validate Discount Response Serialization
    # -----------------------------------------------------------------------
    def test_tc_011_discount_serialization(self, setup_class):
        """
        Verify each discount in the response is serialized with all required fields and nested arrays.
        """
        helper = setup_class
        helper.open_api_docs()
        helper.authorize(VALID_JWT_TOKEN)
        helper.expand_endpoint("GET /api/v1/discounts")
        helper.execute_request()
        status_code = helper.get_response_status_code()
        response = helper.get_response_body()

        assert status_code == 200, f"Expected 200, got {status_code}"
        assert isinstance(response, list), "Response is not a JSON array"

        for discount in response:
            errors = validate_discount_serialization(discount)
            assert not errors, f"Discount serialization validation failed: {errors}"

# ---------------------------------------------------------------------------
# End of Discount API Selenium Test Suite
# ---------------------------------------------------------------------------
"""