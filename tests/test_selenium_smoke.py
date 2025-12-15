def test_selenium_driver_works(driver):
    """
    CI smoke test to verify Selenium + Chrome works in GitHub Actions.
    """
    driver.get("https://www.google.com")
    assert "Google" in driver.title
