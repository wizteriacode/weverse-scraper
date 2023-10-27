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
import undetected_chromedriver as uc
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

# Create a unique directory for this execution to store screenshots and downloads
EXECUTION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S/")
SCREENSHOT_DIR = os.path.join("screenshots", EXECUTION_TIMESTAMP)

ARTISTS = ["newjeansofficial", "riize", "seventeen", "redvelvet"]
# ARTISTS = ["riize"]

def save_urls_to_file(urls, page_type, filename=None):
    if filename is None:
        filename = f"{page_type}_saved_urls.txt"
    with open(filename, 'w') as f:
        for url in urls:
            f.write(url + '\n')

def load_urls_from_file(page_type, filename=None):
    if filename is None:
        filename = f"{page_type}_saved_urls.txt"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def clean_url(url):
    """
    Clean the URL to remove the type parameter.
    """
    base_url = url.split('?')[0]
    return base_url

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

def screenshot(driver, name, directory=SCREENSHOT_DIR):
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

# def scrape_images(driver, artist_name, max_scroll_times=50, scroll_delay=2):
#     scroll_count = 0
#     all_images = set()  # Use a set to avoid duplicate URLs
# 
#     # Load existing URLs
#     existing_urls = {clean_url(url) for url in load_urls_from_file()}
# 
#     while True:
#         # Scroll down
#         driver.execute_script("window.scrollBy(0, 2000);")
#         scroll_count += 1
#         logging.info(f"Scrolled {scroll_count} times.")
# 
#         # Wait for content to load
#         time.sleep(scroll_delay)
# 
#         # Extract post images
#         post_images = driver.find_elements(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
#         post_img_links = {img.get_attribute("src").split("?")[0] for img in post_images}
# 
#         # Update all_images set
#         all_images.update(post_img_links)
# 
#         # If any of the currently found images matches a saved image URL or we've scrolled too many times, break the loop
#         matching_saved_images = [url for url in all_images if url in existing_urls]
#         if matching_saved_images:
#             logging.info(f"Found saved image(s): {matching_saved_images}. Stopping the scroll.")
#             break
#         elif scroll_count >= max_scroll_times:
#             logging.warning(f"Reached maximum scroll times ({max_scroll_times}). Stopping the scroll.")
#             break
# 
#     # Filter out images already saved
#     new_image_urls = list(set(clean_url(url) for url in all_images) - existing_urls)
# 
#     # Create a directory named with the current timestamp if there are new images
#     if new_image_urls:
#         directory_name = f"downloaded_images/{artist_name}/feed/{EXECUTION_TIMESTAMP}"
#         if not os.path.exists(directory_name):
#             os.makedirs(directory_name)
#         logging.info(f"Created directory: {directory_name}")
# 
#         # Download new images
#         for idx, img_url in enumerate(new_image_urls, 1):
#             img_response = requests.get(img_url, stream=True)
#             img_name = os.path.join(directory_name, f"image_{idx}.jpg")
#             with open(img_name, 'wb') as img_file:
#                 for chunk in img_response.iter_content(chunk_size=1024):
#                     img_file.write(chunk)
#             logging.info(f"Downloaded {img_name}")
# 
#         # Update the saved URLs
#         save_urls_to_file(existing_urls.union(new_image_urls))
# 
#     return new_image_urls

def scrape_images(driver, artist_name, max_scroll_times=50, scroll_delay=2):
    scroll_count = 0
    all_images = set()

    # Load existing URLs
    existing_urls = {clean_url(url) for url in load_urls_from_file("feed")}

    while True:
        # Scroll down
        driver.execute_script("window.scrollBy(0, 2000);")
        scroll_count += 1
        logging.info(f"Scrolled {scroll_count} times.")

        # Wait for content to load
        time.sleep(scroll_delay)

        # Extract post images
        post_images = driver.find_elements(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
        post_img_links = {clean_url(img.get_attribute("src")) for img in post_images}

        # Update all_images set
        all_images.update(post_img_links)

        # If any of the currently found images matches a saved image URL or we've scrolled too many times, break the loop
        matching_saved_images = [url for url in post_img_links if url in existing_urls]
        if matching_saved_images:
            logging.info(f"Found saved image(s): {matching_saved_images}. Stopping the scroll.")
            break
        elif scroll_count >= max_scroll_times:
            logging.warning(f"Reached maximum scroll times ({max_scroll_times}). Stopping the scroll.")
            break

    # Filter out images already saved
    new_image_urls = list(all_images - existing_urls)

    # Create a directory named with the current timestamp if there are new images
    if new_image_urls:
        directory_name = f"downloaded_images/{artist_name}/feed/{EXECUTION_TIMESTAMP}"
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)
        logging.info(f"Created directory: {directory_name}")

        # Download new images
        for idx, img_url in enumerate(new_image_urls, 1):
            img_response = requests.get(img_url, stream=True)
            img_name = os.path.join(directory_name, f"image_{idx}.jpg")
            with open(img_name, 'wb') as img_file:
                for chunk in img_response.iter_content(chunk_size=1024):
                    img_file.write(chunk)
            logging.info(f"Downloaded {img_name}")

        # Update the saved URLs
        save_urls_to_file(existing_urls.union(new_image_urls), 'feed')

    return new_image_urls


def scrape_artist_images(driver, artist_name, max_scroll_times=50, scroll_delay=2):
    scroll_count = 0
    all_images = set()  # Use a set to avoid duplicate URLs

    # Load existing URLs
    existing_urls = {clean_url(url) for url in load_urls_from_file("artist")}

    while True:
        # Scroll down
        driver.execute_script("window.scrollBy(0, 2000);")
        scroll_count += 1
        logging.info(f"Scrolled {scroll_count} times.")

        # Wait for content to load
        time.sleep(scroll_delay)

        # Extract post images
        post_images = driver.find_elements(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
        post_img_links = {clean_url(img.get_attribute("src")) for img in post_images}


        # Update all_images set
        all_images.update(post_img_links)

        # If any of the currently found images matches a saved image URL or we've scrolled too many times, break the loop
        matching_saved_images = [url for url in all_images if url in existing_urls]
        if matching_saved_images:
            logging.info(f"Found saved image(s): {matching_saved_images}. Stopping the scroll.")
            break
        elif scroll_count >= max_scroll_times:
            logging.warning(f"Reached maximum scroll times ({max_scroll_times}). Stopping the scroll.")
            break

    # Filter out images already saved
    new_image_urls = list(set(clean_url(url) for url in all_images) - existing_urls)

    # Create a directory named with the current timestamp if there are new images
    if new_image_urls:
        directory_name = f"downloaded_images/{artist_name}/artist/{EXECUTION_TIMESTAMP}"
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)
        logging.info(f"Created directory: {directory_name}")

        # Download new images
        for idx, img_url in enumerate(new_image_urls, 1):
            img_response = requests.get(img_url, stream=True)
            img_name = os.path.join(directory_name, f"image_{idx}.jpg")
            with open(img_name, 'wb') as img_file:
                for chunk in img_response.iter_content(chunk_size=8192):
                    img_file.write(chunk)
            logging.info(f"Saved image {idx} to {img_name}")

    # Save new URLs
    save_urls_to_file(existing_urls.union(new_image_urls), 'artist')

    return new_image_urls

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Set up Chrome options to use the custom User Agent
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"user-agent={user_agent}")
# chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--headless")

# Initialize the WebDriver with the options
driver = uc.Chrome(options=chrome_options)

# Navigate to the login page
driver.get("https://account.weverse.io/ja/login/redirect?client_id=weverse&redirect_uri=https%3A%2F%2Fweverse.io%2FloginResult%3Ftopath%3D%252F")

time.sleep(2)

# Print the current url
logging.info(f"URL: {driver.current_url}")

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

    for artist in ARTISTS:
        logging.info(f"Processing artist: {artist}")

        desired_url_after_login = f"https://weverse.io/{artist}/feed"
        logging.info(f"Navigating to {desired_url_after_login}")
        driver.get(desired_url_after_login)

        time.sleep(5)
        logging.info(f"Taking a screenshot for artist {artist}'s feed after navigation")
        screenshot(driver, f"{artist}_feed_after_login")

        logging.info(f"Starting image scraping for artist {artist}")
        # Scrape images from the artist's feed page
        scraped_feed_image_urls = scrape_images(driver, artist)
        logging.info(f"Scraped {len(scraped_feed_image_urls)} new images from {artist}'s feed.")

        # Navigate to the artist's artist page
        artist_page_url = f"https://weverse.io/{artist}/artist"
        driver.get(artist_page_url)

        time.sleep(5)
        logging.info(f"Taking a screenshot for artist {artist}'s artist page after navigation")
        screenshot(driver, f"{artist}_artist_page_after_login")

        # Scrape images from the artist's artist page
        scraped_artist_image_urls = scrape_artist_images(driver, artist)
        logging.info(f"Scraped {len(scraped_artist_image_urls)} new images from {artist}'s artist page.")

        logging.info(f"Finished processing artist: {artist}")

# Add other actions or wait as necessary

# Close the browser
driver.close()

