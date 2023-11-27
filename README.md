# HARMONY Documentation

## Overview

The scraper is a Python script (`scraper.py`) designed to scrape data. The scraped data includes information about composers and their compositions, which is then stored in a SQLite database.

Additionally, the `harmony.py` script is a companion to the scraper. It utilizes the Dash framework to create a web-based visualization of the scraped data, allowing users to explore various insights and statistics about composers and compositions.

## Table of Contents

1. [scraper.py](#scraperpy)
    - [File Structure](#file-structure)
    - [Usage](#usage)
    - [Dependencies](#dependencies)
    - [Configuration](#configuration)
    - [Functions and Classes](#functions-and-classes)
        - [Main Functions](#main-functions)
        - [Database Functions](#database-functions)
        - [Utility Functions](#utility-functions)
        - [Database Checking Functions](#database-checking-functions)
        - [Database Insertion Functions](#database-insertion-functions)
        - [Processing Functions](#processing-functions)
        - [Extracting Functions](#extracting-functions)
        - [Check for robots.txt](#check-for-robotstxt)
        - [Main Function](#main-function)
2. [harmony.py](#harmonypy)
    - [File Structure](#file-structure-1)
    - [Usage](#usage-1)
    - [Dependencies](#dependencies-1)
    - [Configuration](#configuration-1)
    - [Functions and Classes](#functions-and-classes-1)
        - [Fetch and Extract Data](#fetch-and-extract-data)
        - [Wordcloud Generation](#wordcloud-generation)
        - [Top 10 Categories](#top-10-categories)
        - [Frequency Visualization](#frequency-visualization)
        - [Dash App Creation](#dash-app-creation)
        - [Main Execution](#main-execution)

## scraper.py

### File Structure

- **scraper.py**: Main script for scraping data.
- **harmony.db**: SQLite database file to store scraped data.

### Usage

Run `scraper.py` to initiate the scraping process. The script will retrieve information about composers and compositions, store it in the `harmony.db` database, and mark the processed composers.

### Dependencies

- `urllib.request`
- `urllib.parse`
- `robotparser`
- `BeautifulSoup`
- `collections`
- `sqlite3`
- `re`
- `json`
- `requests`
- `signal`
- `gzip`
- `io`
- `sys`

### Configuration

- `DB_FILE_PATH`: Path to the SQLite database file.
- `URL_BASE`: Base URL.
- `MAIN_URL`: Main URL for wiki.
- `START_URL`: Starting URL for scraping.

### Functions and Classes

#### Main Functions

- `main()`: Entry point of the script.
- `exit_program()`: Exits the program with a message.
- `signal_handler()`: Handles Ctrl+C to exit gracefully.
- `create_database()`: Creates database tables if they don't exist.
- `get_soup()`: Retrieves HTML content from a given URL.
- `scrape_data()`: Initiates the scraping process.

#### Database Functions

- `insert_composer()`: Inserts a composer into the database.
- `insert_composition()`: Inserts a composition into the database.
- `insert_item()`: Inserts an item into a specified table.

#### Utility Functions

- `get_soup()`: Retrieves HTML content from a given URL.
- `extract_birth_death_year()`: Extracts birth and death years from a text.
- `is_scraping_allowed()`: Checks if scraping is allowed for a given URL.

#### Database Checking Functions

- `composer_is_saved()`: Checks if a composer is already saved in the database.
- `composition_is_saved()`: Checks if a composition is already saved in the database.
- `composer_is_processed()`: Checks if a composer is already processed.

#### Database Insertion Functions

- `insert_composer()`: Inserts a composer into the database.
- `insert_composition()`: Inserts a composition into the database.
- `insert_item()`: Inserts an item into a specified table.

#### Processing Functions

- `process_composer()`: Processes a composer and their compositions.
- `process_composition()`: Processes a composition.

#### Extracting Functions

- `extract_text(element)`: Extracts text from an HTML element.
- `extract_data_mapping()`: Extracts data mapping from general information tables.

#### Check for robots.txt

- `is_scraping_allowed()`: Checks if scraping is allowed for a given URL.

#### Main Function

- `main()`: Entry point of the script.

## harmony.py

### File Structure

- **harmony.py**: Main script for visualizing data using Dash.
- **database/harmony.db**: SQLite database file containing scraped data.
- **media/face.png**: Image file for the face mask used in word clouds.
- **media/music.png**: Image file for the music mask used in word clouds.

### Usage

Run `harmony.py` to start the Dash app. The app allows users to explore visualizations and insights about composers and compositions based on the scraped data.

### Dependencies

- `sqlite3`
- `Dash`
- `dcc`
- `html`
- `Input`
- `Output`
- `Counter`
- `defaultdict`
- `plotly.express`
- `WordCloud`
- `base64`
- `BytesIO`
- `Image`
- `numpy`
- `plotly.graph_objects`

### Configuration

- `DB_FILE_PATH`: Path to the SQLite database file.
- `FACE_IMG_PATH`: Path to the face mask image file.
- `MUSIC_IMG_PATH`: Path to the music mask image file.

### Functions and Classes

#### Fetch and Extract Data

- `fetch_data()`: Connects to the SQLite database and fetches data.
- `extract_data()`: Extracts nested information with error handling.

#### Wordcloud Generation

- `generate_wordcloud()`: Generates a word cloud based on composer or composition names.

#### Top 10 Categories

- `generate_top_10()`: Generates a scatter plot of the top 10 categories.

#### Frequency Visualization

- `generate_frequency()`: Generates a stacked bar chart for frequency visualization.

#### Dash App Creation

- `create_dash_app()`: Creates a Dash app with layout and callbacks.

#### Main Execution

- Fetches and extracts data from the SQLite database.
- Initializes wordcloud masks.
- Defines callbacks for Dash app.
- Runs the Dash app.

**Note**: Ensure that the necessary dependencies are installed before running the scripts. You can install them using `pip install -r requirements.txt`.
