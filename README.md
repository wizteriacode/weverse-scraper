# weverse-scraper

This Python script logs into Weverse, navigates to specified feeds and artist pages, and then scrapes and downloads images. Only new images that haven't been previously downloaded are saved. Once the images are scraped and downloaded, they are synced to a specified Dropbox directory.

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Functions](#functions)
- [Dropbox Sync](#dropbox-sync)

## Requirements

- Python 3.x
- Selenium
- Chrome WebDriver
- undetected_chromedriver
- dotenv
- requests
- dropbox

## Setup

1. Clone this repository:
   ```
   git clone <repository_url>
   ```

2. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and provide your Weverse credentials and Dropbox token:
   ```
   EMAIL=your_email_here
   PASSWORD=your_password_here
   DROPBOX_TOKEN=your_dropbox_token_here
   ```

## Usage

Run the script:
```
python3 scraper.py
```

This will perform the following actions:
- Launch Chrome WebDriver.
- Navigate to Weverse's login page and log in using the credentials from `.env`.
- Navigate to the specified feeds and artist pages of multiple artists after logging in.
- Scroll through each page until it encounters previously saved images or reaches a maximum limit.
- Scrape and download only new images found by cross-referencing with a local file that tracks previously downloaded images.

Images will be saved in a directory structure based on the page type:

- For feeds: `downloaded_images/ARTIST_NAME/feed/downloaded_images_TIMESTAMP`
- For artist pages: `downloaded_images/ARTIST_NAME/artist/downloaded_images_TIMESTAMP`

Where `TIMESTAMP` is the current date and time.

Screenshots taken during the script's execution will be saved in the `screenshots` directory with filenames in the format: `ARTIST_NAME_PAGE_TYPE_after_login_TIMESTAMP.png`.

## Functions

- `get_h1_text(driver)`: Extracts the text inside the first `<h1>` tag on the current page of the given driver.
- `screenshot(driver, name, directory="./screenshots/")`: Saves a screenshot of the current state of the driver.
- `scrape_images(driver, artist_name, max_scroll_times=50, scroll_delay=2)`: Scrolls, scrapes images from the feed, and downloads them until encountering previously saved images or reaching the maximum scroll limit.
- `scrape_artist_images(driver, artist_name, max_scroll_times=50, scroll_delay=2)`: Scrolls, scrapes images from the artist page, and downloads them until encountering previously saved images or reaching the maximum scroll limit.

Both scraping functions ensure only new images are downloaded by checking against a local file of previously downloaded image URLs.

## Maintenance

The script maintains a local file for tracking downloaded image URLs. To ensure that this file doesn't grow indefinitely, the script is designed to:

1. Trim the file by retaining only the most recent URLs when the number of saved URLs exceeds a specified limit.
2. Log the removed URLs for reference and documentation purposes.
3. Provide statistics on the number of removed URLs.

This automatic maintenance ensures efficient cross-referencing of new images without letting the saved URLs file become overly large.

## Dropbox Sync

After successfully scraping and downloading images from Weverse, the script initiates a sync process to a specified Dropbox directory. The Dropbox syncing is handled by the `DropboxSyncBot` class, which checks for new directories and files to sync while avoiding redundant uploads.

The script will send an alert to a Discord channel via a webhook upon successful creation of a new directory in Dropbox. The alert provides details such as the artist, page type, and a direct link to the newly created directory in Dropbox.

To set up Dropbox sync:
1. Ensure you have the `DROPBOX_TOKEN` set in the `.env` file.
2. The script will sync the downloaded images to a directory structure in Dropbox that mirrors the local structure.
