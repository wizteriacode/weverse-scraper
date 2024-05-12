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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
import undetected_chromedriver as uc
from dotenv import load_dotenv

from dropbox_sync import DropboxSyncBot

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

ENABLE_DROPBOX_SYNC = os.getenv("ENABLE_DROPBOX_SYNC", "True").lower() == "true"

if ENABLE_DROPBOX_SYNC:
    logging.info("Dropbox sync is ENABLED.")
    DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
    bot = DropboxSyncBot(DROPBOX_TOKEN, DISCORD_WEBHOOK_URL)
else:
    logging.info("Dropbox sync is DISABLED.")

MAX_FEED_URLS = int(os.getenv("MAX_FEED_URLS", 1000))
MAX_ARTIST_URLS = int(os.getenv("MAX_ARTIST_URLS", 1000))

# Create a unique directory for this execution to store screenshots and downloads
EXECUTION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S/")
SCREENSHOT_DIR = os.path.join("screenshots", EXECUTION_TIMESTAMP)

ARTISTS = [artist.strip() for artist in os.getenv("ARTISTS").split(',')]
SKIP_FEED_ARTISTS = set(artist.strip() for artist in os.getenv('SKIP_FEED_ARTISTS', '').split(','))
SKIP_ARTIST_PAGE_ARTISTS = set(artist.strip() for artist in os.getenv('SKIP_ARTIST_PAGE_ARTISTS', '').split(','))

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

def send_discord_alert(title, description):
    """
    Send an alert message to a Discord channel via webhook in the form of an embed.

    Args:
    - title: The title of the embed.
    - description: The description/content of the embed.
    """
    payload = {
        'embeds': [{
            'title': title,
            'description': description,
            'color': 16711680  # Red color for error
        }]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        logging.info(f"Sent alert to Discord: {title} - {description}")
    else:
        logging.error(f"Failed to send alert to Discord. Status code: {response.status_code}, Response: {response.text}")

def clean_url(url):
    """
    Clean the URL to remove the type parameter.
    """
    base_url = url.split('?')[0]
    return base_url

def trim_saved_urls(filename, max_urls=1000):
    """
    Trim the saved URLs file to keep only the most recent URLs.

    Args:
    - filename: The file containing the saved URLs.
    - max_urls: The maximum number of URLs to retain. Older URLs beyond this number will be removed.
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            urls = f.readlines()

        # Check if the number of URLs exceeds the maximum allowed
        if len(urls) > max_urls:
            # Split URLs into those to retain and those to remove
            removed_urls = urls[:-max_urls]
            trimmed_urls = urls[-max_urls:]

            # Log the number of removed URLs and the actual URLs
            logging.info(f"Removing {len(removed_urls)} URLs:")
            for url in removed_urls:
                logging.info(url.strip())

            # Write the trimmed URLs back to the file
            with open(filename, 'w') as f:
                f.writelines(trimmed_urls)
            logging.info(f"Trimmed saved URLs to the last {max_urls} entries.")

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

def click_confirmation_button(driver):
    try:
        logging.info("Checking for alert window...")
        alert_window = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='alert']"))
        )
        if alert_window:
            logging.info("Alert window found. Checking for confirmation button...")
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='alert'] button[type='button']"))
            )
            confirm_button.click()
            logging.info("Confirmation button clicked.")
            time.sleep(10)
            return True
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        logging.warning(f"Confirmation button click intercepted or not found: {e}")
        return False
    except TimeoutException:
        logging.warning(f"Timeout waiting for alert window or confirmation button")
        return False

def click_submit_button(driver):
    try:
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()
        logging.info("Submit button clicked.")
        time.sleep(10)
        return True
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        logging.warning(f"Submit button click intercepted or not found: {e}")
        return False

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

def scrape_images(driver, artist_name, max_scroll_times=50, scroll_delay=2):
    scroll_count = 0
    all_images = set()

    # Load existing URLs
    existing_urls = {clean_url(url) for url in load_urls_from_file("feed")}

    # Check the first three posts for pinned posts
    pinned_img_links = []
    time.sleep(2)  # Wait for a short duration to ensure that dynamic content is loaded
    first_three_posts = driver.find_elements(By.CSS_SELECTOR, ".PostListItemView_post_item__XJ0uc")[:10]
    for post in first_three_posts:
        date_element = post.find_element(By.CSS_SELECTOR, ".PostHeaderView_date__XJXBZ")
        if "おすすめ投稿" in date_element.text or "Recommended post" in date_element.text:
            try:
                img_element = post.find_element(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
                img_url = clean_url(img_element.get_attribute("src"))
                pinned_img_links.append(img_url)
                logging.info(f"Identified pinned post with image URL: {img_url}. This image will be skipped.")
            except NoSuchElementException:
                logging.info(f"Identified a pinned post without an image. Skipping this post.")
                continue

    while True:
        # Scroll down
        driver.execute_script("window.scrollBy(0, 2000);")
        scroll_count += 1
        logging.info(f"Scrolled {scroll_count} times.")

        # Wait for content to load
        time.sleep(scroll_delay)

        # Extract post images
        post_images = driver.find_elements(By.CSS_SELECTOR, ".PostPreviewImageView_post_image__zLzXH")
        post_img_links = {clean_url(img.get_attribute("src")) for img in post_images} - set(pinned_img_links)

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

        # Trim the saved URLs to keep only the most recent ones
        trim_saved_urls(f"feed_saved_urls.txt", max_urls=MAX_FEED_URLS)

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

    # Trim the saved URLs to keep only the most recent ones
    trim_saved_urls(f"artist_saved_urls.txt")
    trim_saved_urls(f"artist_saved_urls.txt", max_urls=MAX_ARTIST_URLS)

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

# Handle additional login steps if necessary


if h1_after_login != "weverse":
    logging.info("There's something wrong with the login process")

    try:
        logging.info("Checking for email code input...")
        email_code_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'otpCode'))
        )
        if email_code_input:
            logging.info("Email code input found. Prompting user for email code...")
            email_code = input("Enter the code sent to your email: ")
            email_code_input.send_keys(email_code)
            logging.info("Email code entered.")

            # Always try to click the confirmation button first
            click_confirmation_button(driver)

            logging.info("Trying to click submit button...")
            if click_submit_button(driver):
                logging.info("Checking for confirmation button again...")
                click_confirmation_button(driver)
    except NoSuchElementException:
        logging.info("No additional login step required.")

time.sleep(10)

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
        if artist not in SKIP_FEED_ARTISTS:
            scraped_feed_image_urls = scrape_images(driver, artist)
            logging.info(f"Scraped {len(scraped_feed_image_urls)} new images from {artist}'s feed.")
        else:
            logging.info(f"Skipping scraping for {artist}'s feed as per configuration.")

        # Navigate to the artist's artist page
        artist_page_url = f"https://weverse.io/{artist}/artist"
        driver.get(artist_page_url)

        time.sleep(5)
        logging.info(f"Taking a screenshot for artist {artist}'s artist page after navigation")
        screenshot(driver, f"{artist}_artist_page_after_login")

        # Scrape images from the artist's artist page
        if artist not in SKIP_ARTIST_PAGE_ARTISTS:
            scraped_artist_image_urls = scrape_artist_images(driver, artist)
            logging.info(f"Scraped {len(scraped_artist_image_urls)} new images from {artist}'s artist page.")
        else:
            logging.info(f"Skipping scraping for {artist}'s artist page as per configuration.")

        logging.info(f"Finished processing artist: {artist}")

# After scraping for all artists, start the syncing process
if ENABLE_DROPBOX_SYNC:
    for artist in ARTISTS:
        local_directory = f"./downloaded_images/{artist}"
        dropbox_directory = f"/weverse/{artist}"

        try:
            logging.info(f"Starting Dropbox sync for artist {artist}...")
            bot.sync_folder(local_directory, dropbox_directory)
            logging.info(f"Completed Dropbox sync for artist {artist}.")
        except Exception as e:
            error_title = f"Error for Artist: {artist}"
            error_description = f"Error during Dropbox sync: {e}"
            logging.error(f"{error_title} - {error_description}")
            send_discord_alert(error_title, error_description)

# Close the browser
driver.close()

