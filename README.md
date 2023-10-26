# weverse-scraper

This Python script logs into Weverse, navigates to a specified feed, and then scrapes and downloads images from the user's feed.

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
- Navigate to the specified feed after logging in.
- Scroll through the feed to load more content.
- Scrape and download only new images found on the feed by cross-referencing with a local file that tracks downloaded images.

Images will be saved in a directory named `downloaded_images_TIMESTAMP`, where `TIMESTAMP` is the current date and time.

## Functions

- `get_h1_text(driver)`: Extracts the text inside the first `<h1>` tag on the current page of the given driver.
- `screenshot(driver, name, directory="./screenshots/")`: Saves a screenshot of the current state of the driver.
- `scrape_images(driver, scroll_times=3, scroll_delay=2)`: Scrolls, scrapes images, and downloads them to a local directory, ensuring only new images are downloaded.
