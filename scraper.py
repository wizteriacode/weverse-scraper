import os
import logging
import time
from datetime import datetime

import requests

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

def screenshot(driver, name, directory="./screenshots/"):
    """
    Save a screenshot of the current state of the driver.

    Args:
    - driver: The Selenium WebDriver instance.
    - directory: The directory where the screenshot will be saved. Defaults to "./screenshots/".

    Returns:
    - The path to the saved screenshot.
    """
    # Ensure the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")
    
    # Generate a timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_name = f"{directory}{name}_{timestamp}.png"
    
    # Save the screenshot
    driver.save_screenshot(screenshot_name)
    logging.info(f"Saved screenshot as: {screenshot_name}")
    
    return screenshot_name

def scrape_images(driver, scroll_times=3, scroll_delay=2):
    for i in range(scroll_times):
        # Scroll down
        driver.execute_script("window.scrollBy(0, 2000);")
        logging.info(f"Scrolled {i + 1} out of {scroll_times} times.")

        # Wait for content to load
        time.sleep(scroll_delay)
        logging.info(f"Waited for {scroll_delay} seconds after scrolling.")

    # Extract profile thumbnail image
    profile_thumbnails = driver.find_elements(By.CSS_SELECTOR, ".ProfileThumbnailView_thumbnail__8W3E7 img")
    profile_images = [img.get_attribute("src") for img in profile_thumbnails]
    # logging.info(f"Found {len(profile_images)} profile thumbnail images.")

    # Extract post images
    post_images = driver.find_elements(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
    post_img_links = [img.get_attribute("src") for img in post_images]
    logging.info(f"Found {len(post_img_links)} post images.")

    # Combine and return the lists
    all_images = profile_images + post_img_links

    # Create a directory named with the current timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    directory_name = f"downloaded_images_{timestamp}"
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    logging.info(f"Created directory: {directory_name}")

    # Download images
    for idx, img_url in enumerate(all_images, 1):
        img_response = requests.get(img_url, stream=True)
        img_name = os.path.join(directory_name, f"image_{idx}.jpg")
        with open(img_name, 'wb') as img_file:
            for chunk in img_response.iter_content(chunk_size=1024):
                img_file.write(chunk)
        logging.info(f"Downloaded {img_name}")

    return all_images

# chromedriver_autoinstaller.install()
# logging.info("Chromedriver installed.")

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
logging.info(f"h1: {get_h1_text(driver)}")


# Find and click the login button
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
)
login_button.click()

time.sleep(10)

screenshot(driver, "after_login")

h1_after_login = get_h1_text(driver)
logging.info(f"h1: {get_h1_text(driver)}")

if h1_after_login == "weverse":
    logging.info("Successfully logged in!")
    # Navigate to the desired page after logging in
    desired_url_after_login = "https://weverse.io/newjeansofficial/feed"
    driver.get(desired_url_after_login)
    time.sleep(5)
    screenshot(driver, "desired_url_agter_login")
    scraped_images = scrape_images(driver, scroll_times=10)
    # logging.info(scraped_images)

# Add other actions or wait as necessary

# Close the browser
driver.close()
