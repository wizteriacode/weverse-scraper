import os
import logging
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import chromedriver_autoinstaller
import undetected_chromedriver as uc
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_h1_text(driver):
    """
    Extracts the text inside the first <h1> tag on the current page of the given driver.

    Args:
    - driver: The Selenium WebDriver instance.

    Returns:
    - The text inside the <h1> tag or None if the tag is not found.
    """
    try:
        h1_text = driver.find_element(By.TAG_NAME, 'h1').text
        return h1_text
    except Exception as e:
        logging.error(f"Error retrieving <h1> text: {e}")
        return None

# chromedriver_autoinstaller.install()
logging.info("Chromedriver installed.")

# Initialize the Chrome WebDriver
# driver = webdriver.Chrome()

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Set up Chrome options to use the custom User Agent
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"user-agent={user_agent}")
# chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--headless")

# Initialize the WebDriver with the options
driver = uc.Chrome(options=chrome_options)

# Print the current url
logging.info(driver.current_url)

# Navigate to the login page
driver.get("https://account.weverse.io/ja/login/redirect?client_id=weverse&redirect_uri=https%3A%2F%2Fweverse.io%2FloginResult%3Ftopath%3D%252F")

time.sleep(2)

# Use WebDriverWait to ensure the email input is present and interactable
email_elem = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.NAME, 'email'))
)
email_elem.send_keys(EMAIL)

# Add a delay or wait for the password field to be available again after entering the email
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'password'))
)

time.sleep(2)

# Similarly for the password input
password_elem = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.NAME, 'password'))
)
# Find the password input again
password_elem = driver.find_element(By.NAME, 'password')
password_elem.send_keys(PASSWORD)

time.sleep(2)

# Print the current url
logging.info(driver.current_url)

# Print the content of the <h1> tag
logging.info(get_h1_text(driver))


# Find and click the login button
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
)
login_button.click()

time.sleep(10)

# Print the content of the <h1> tag
logging.info(get_h1_text(driver))

# Define the directory
screenshot_directory = "./screenshots/"

# Ensure the directory exists, if not, create it
if not os.path.exists(screenshot_directory):
    os.makedirs(screenshot_directory)

# Generate a timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
screenshot_name = f"{screenshot_directory}weverse_{timestamp}.png"

# Save the screenshot with the timestamped filename in the specified directory
driver.save_screenshot(screenshot_name)

# Add other actions or wait as necessary

# Close the browser
driver.close()

