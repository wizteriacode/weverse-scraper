# weverse-scraper

This Python script logs into Weverse, navigates to a specified feed, and then scrapes and downloads images from the user's feed. Only new images that haven't been previously downloaded are saved.

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Functions](#functions)

## Requirements

- Python 3.x
- Selenium
- Chrome WebDriver
- undetected_chromedriver
- dotenv
- requests

## Setup

1. Clone this repository:
   ```
   git clone <repository_url>
   ```

2. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and provide your Weverse credentials:
   ```
   EMAIL=your_email_here
   PASSWORD=your_password_here
   ```

## Usage

Run the script:
```
python scraper.py
```

This will perform the following actions:
- Launch Chrome WebDriver.
- Navigate to Weverse's login page and log in using the credentials from `.env`.
- Navigate to the specified feeds of multiple artists after logging in.
- Scroll through each feed until it encounters previously saved images or reaches a maximum limit.
- Scrape and download only new images found on the feed by cross-referencing with a local file that tracks previously downloaded images.

Images will be saved in a directory structure: `downloaded_images/ARTIST_NAME/downloaded_images_TIMESTAMP`, where `TIMESTAMP` is the current date and time. Screenshots taken during the script's execution will be saved in the `screenshots` directory with filenames in the format: `ARTIST_NAME_feed_after_login_TIMESTAMP.png`.

## Functions

- `get_h1_text(driver)`: Extracts the text inside the first `<h1>` tag on the current page of the given driver.
- `screenshot(driver, name, directory="./screenshots/")`: Saves a screenshot of the current state of the driver.
- `scrape_images(driver, artist_name, max_scroll_times=50, scroll_delay=2)`: Continuously scrolls, scrapes images, and downloads them to a local directory until it encounters images that have been previously saved or reaches the maximum scroll limit. This function ensures only new images are downloaded by checking against a local file of previously downloaded image URLs.

