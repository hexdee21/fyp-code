from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_admin_login():
    driver = webdriver.Chrome()
    driver.get("http://localhost:5173/login")

    # ✅ Create wait object
    wait = WebDriverWait(driver, 10)

    # Locate fields
    email = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password = wait.until(EC.presence_of_element_located((By.ID, "password")))
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))

    # Actions
    email.send_keys("admin@example.com")
    password.send_keys("admin123")
    login_btn.click()

    # Assertion: admin dashboard loaded
    wait.until(EC.url_contains("/dashboard"))

    driver.quit()
