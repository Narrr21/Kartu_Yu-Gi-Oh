﻿# Yu-Gi-Oh! TCG Card Database

This is a desktop application built with PyQt5 for searching Yu-Gi-Oh! Trading Card Game (TCG) cards with fuzzy matching capabilities. The application scrapes card data from a specified online database and allows users to search for cards by name, effect, type, or attribute.

## Features

* **Fuzzy Search**: Find cards even with partial or slightly incorrect spellings using fuzzy string matching.
* **Single Card Search**: Quickly find the best match for a specific card.
* **Multi-Card Search**: Discover multiple cards that are similar to your search query.
* **Data Scraping**: Scrapes card data from the Yu-Gi-Oh! database website.
* **Caching**: Caches scraped card data locally for faster subsequent loading and offline access.
* **Interactive UI**: Built with PyQt5 for a user-friendly graphical interface.
* **Toast Notifications**: Provides informative toast messages for application events.

## Installation

To set up and run this application, follow these steps:

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone [https://github.com/your-username/Kartu_Yu-Gi-Oh.git](https://github.com/your-username/Kartu_Yu-Gi-Oh.git)
    cd Kartu_Yu-Gi-Oh
    ```

2.  **Create a virtual environment :**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    * On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    * `beautifulsoup4==4.13.4`
    * `fuzzywuzzy==0.18.0`
    * `python-Levenshtein==0.27.1`
    * `requests==2.32.4`
    * `PyQt5`

## Usage

1.  **Run the application:**
    ```bash
    python src/main.py
    ```

2.  **Initial Data Scraping:**
    * The first time you run the application, it will automatically scrape pack URLs and then card data. This process might take some time depending on your internet connection and the `MAX_PACKS_TO_SCRAPE` setting in `src/config.py`.
    * A progress bar and status messages in the status bar will indicate the scraping progress.
    * Once scraping is complete, the data will be cached locally in `json/card_cache.json` for faster loading in subsequent runs.

3.  **Searching Cards:**
    * Enter your search query in the text box. You can search by card name, description, type, or attribute.
    * Click "Search" for the best single match.
    * Click "Multi Search" to find multiple potential matches.
    * For multi-search, you can include required keywords by enclosing them in `#` (e.g., `Dark Magician #spell#`).

4.  **Menu Options:**
    * **File > Refresh Database**: Clears the existing cache and re-scrapes all data from scratch.
    * **File > Clear Cache**: Deletes the local card data cache.
    * **File > Exit**: Closes the application.
    * **Help > About**: Displays information about the application.

## Configuration

The `src/config.py` file contains important settings you can modify:

* `CACHE_FILE`                  : Path to the JSON file used for caching card data.
* `PACK_URLS_FILE`              : Path to the JSON file storing scraped pack URLs.
* `ICON_FILE`                   : Path to the application icon.
* `MAIN_SEARCH_PAGE_URL`        : The base URL for scraping pack information.
* `MAX_PACKS_TO_SCRAPE`         : Limits the number of packs to scrape (set to `None` to scrape all).
* `USER_AGENT`                  : User-Agent string for web requests.
* `FUZZY_SCORE_CUTOFF_SINGLE`   : Minimum fuzzy score for a single best match.
* `FUZZY_SCORE_CUTOFF_MULTI`    : Minimum fuzzy score for multiple matches.
* `MULTI_SEARCH_LIMIT`          : Maximum number of results for multi-search (set to `None` for no limit).

## Authors

Nadhif Al Rozin
