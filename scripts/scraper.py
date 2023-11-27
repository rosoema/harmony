import urllib.request
from urllib.parse import urljoin, quote
from urllib import robotparser
from bs4 import BeautifulSoup
from collections import namedtuple
import sqlite3
import re
import json
import requests
import signal
import gzip
import io
import sys

# Constants
CATEGORY_BASE = "Category:"
COMPOSERS_TOP_BASE = "Composers#fcfrom:Top"

DB_FILE_PATH = "../database/harmony.db"

URL_BASE = "https://imslp.org/"
MAIN_URL = f"{URL_BASE}wiki/"
START_URL = f"{MAIN_URL}{CATEGORY_BASE}{COMPOSERS_TOP_BASE}"

# Namedtuples
Composer = namedtuple("Composer", ["id", "full_name", "birth_year", "death_year"])
Composition = namedtuple("Composition", ["id", "full_name", "work_title", "composer", "composer_id", "key_id", "instrumentation_id", "piece_style_id", "language_id"])

# Global variables
session = requests.Session()
conn = sqlite3.connect(DB_FILE_PATH)

def exit_program():
    print("Exiting...")
    sys.exit(0)

def main():
    try:
        print("Welcome!")
        
        user_input = input("Do you want to exit scrapping? (y/n): ")
        if user_input.lower() == "y":
            exit_program()
                
    except Exception as e:
        print(f"An error occurred: {e}")
        exit_program()

def signal_handler(sig, frame):
    print("Ctrl+C detected. Exiting.")
    main()

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Database functions
def create_database():
    print("Creating database tables if not exist.")
    with conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Composers
                  (id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, birth_year INTEGER, death_year INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  processed INTEGER DEFAULT 0)''')

        c.execute('''CREATE TABLE IF NOT EXISTS Keys
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS Instrumentations
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS Styles
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS Languages
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS Compositions
                  (id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, work_title TEXT,
                  composer_id INTEGER, key_id INTEGER, instrumentation_id INTEGER, piece_style_id INTEGER, language_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (composer_id) REFERENCES Composers (id),
                  FOREIGN KEY (key_id) REFERENCES Keys (id),
                  FOREIGN KEY (instrumentation_id) REFERENCES Instrumentations (id),
                  FOREIGN KEY (piece_style_id) REFERENCES Styles (id),
                  FOREIGN KEY (language_id) REFERENCES Languages (id))''')

# Utility functions
def get_soup(url):
    print(f"Retrieving HTML content from {url}")
    with session.get(url) as response:
        html = response.text
    soup = BeautifulSoup(html, "html.parser")
    return soup

# Database checking functions
def composer_is_saved(full_name):
    with conn:
        c = conn.cursor()
        c.execute("SELECT id FROM Composers WHERE full_name = ?", (full_name,))
        return c.fetchone() is not None

def composition_is_saved(full_name):
    with conn:
        c = conn.cursor()
        c.execute("SELECT id FROM Compositions WHERE full_name = ?", (full_name,))
        return c.fetchone() is not None

def composer_is_processed(full_name):
    with conn:
        c = conn.cursor()
        c.execute("SELECT processed FROM Composers WHERE full_name = ?", (full_name,))
        result = c.fetchone()
        return result is not None and result[0] == 1

# Database insertion functions
def insert_composer(composer):
    if not composer_is_saved(composer.full_name):
        with conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Composers (full_name, birth_year, death_year) VALUES (?, ?, ?)",
                           (composer.full_name, composer.birth_year, composer.death_year))

def insert_composition(composition):
    with conn:
        cursor = conn.cursor()
        composer_id = cursor.execute("SELECT id FROM Composers WHERE full_name = ?", (composition.composer,)).fetchone()
        if composer_id:
            composer_id = composer_id[0]
            cursor.execute("INSERT INTO Compositions (full_name, work_title, composer_id, key_id, instrumentation_id, piece_style_id, language_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (composition.full_name, composition.work_title, composer_id, composition.key_id, composition.instrumentation_id, composition.piece_style_id, composition.language_id))

def insert_item(table_name, item_name):
    if item_name is None:
        return None

    with conn:
        cursor = conn.cursor()

        cursor.execute(f"INSERT OR IGNORE INTO {table_name} (name) VALUES (?)", (item_name,))
        cursor.execute(f"SELECT id FROM {table_name} WHERE name = ?", (item_name,))

        item_id = cursor.fetchone()

        return item_id[0] if item_id else None

# Processing functions
def process_composer(composer_full_name, composer_link):
    composer_soup = get_soup(composer_link)
    composer_header = composer_soup.select(".cp_firsth")
    birth_year, death_year = (extract_birth_death_year(composer_header[0].text) if composer_header else (None, None))
    composer = Composer(id=None, full_name=composer_full_name, birth_year=birth_year, death_year=death_year)
    insert_composer(composer)

    if is_scraping_allowed(MAIN_URL):
        compositions_script_tag = composer_soup.find("script", string=re.compile("catpagejs"))
        compositions_script_str = str(compositions_script_tag)
        compositions_pattern = re.compile(r'catpagejs,{"p1":(.*?)}\);')
        compositions_match = compositions_pattern.search(compositions_script_str)
        compositions_data_str = compositions_match.group(1)
        compositions_data = json.loads(compositions_data_str)

        for composition_letter, compositions in compositions_data.items():
            for composition_full_name in compositions:
                print(f"Processing composition: {composition_full_name}")
                composition_full_name = composition_full_name.split("|")[0]

                composition_link = MAIN_URL + quote(composition_full_name.replace(" ", "_"))
                
                try:
                    process_composition(composer, composition_full_name, composition_link)

                except Exception as comp_err:
                    print(f"Error processing composition {composition_full_name}: {comp_err}")
                    continue

def process_composition(composer, composition_full_name, composition_link):
    with conn:
        if not composition_is_saved(composition_full_name):
            composition_soup = get_soup(composition_link)

            general_info_table = composition_soup.select(".wi_body table")
    
            data_mapping = extract_data_mapping(general_info_table)

            key_id = insert_item("Keys", data_mapping["Key"])
            instrumentation_id = insert_item("Instrumentations", data_mapping["Instrumentation"])
            piece_style_id = insert_item("Styles", data_mapping["Piece Style"])
            language_id = insert_item("Languages", data_mapping["Language"])

            composition = Composition(id=None, full_name=composition_full_name, work_title=data_mapping['Work Title'], composer=composer.full_name, composer_id=None, key_id=key_id, instrumentation_id=instrumentation_id, piece_style_id=piece_style_id, language_id=language_id)
            insert_composition(composition)

# Extracting functions
def extract_text(element):
    if hasattr(element, 'get'):
        if 'ms555' in element.get('class', []):
            return ''
    if hasattr(element, 'contents'):
        return ''.join(extract_text(child) for child in element.contents)
    else:
        return str(element)

def extract_data_mapping(general_info_table):
    desired_headers = ["Key", "Instrumentation", "Piece Style", "Work Title", "Language"]
    data_mapping = {"Key": None, "Instrumentation": None, "Piece Style": None, "Work Title": None, "Language": None}

    for table in general_info_table:
        for row in table.find_all("tr"):
            headers = [extract_text(header).strip() for header in row.find_all("th")]
            data = [data.get_text(separator=", ", strip=True) for data in row.find_all("td")]

            for header in desired_headers:
                index = headers.index(header) if header in headers else None
                data_is_acceptable = index is not None and all(substring not in data[index].lower() for substring in ['unknown', 'see below', 'comments', 'category'])

                if data_is_acceptable:
                    data_mapping[header] = data[index]

    return data_mapping

def extract_birth_death_year(text):
    if "fl." in text:
        return None, None

    year_pattern = re.compile(r"\b(\d{4})\b")
    years = re.findall(year_pattern, text)
    birth_year = int(years[0]) if years else None
    death_year = int(years[1]) if len(years) > 1 else None
    
    return birth_year, death_year

# Check for robots.txt 
def is_scraping_allowed(target_url):
    rp = robotparser.RobotFileParser()
    robots_url = urljoin(URL_BASE, '/robots.txt')
    request = urllib.request.Request(robots_url, headers={'Accept-Encoding': 'gzip'})

    try:
        with urllib.request.urlopen(request) as response:
            content_encoding = response.info().get('Content-Encoding')
            if content_encoding == 'gzip':
                with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as f:
                    data = f.read().decode('utf-8')
            else:
                data = response.read().decode('utf-8')

        rp.parse(data.splitlines())
        return rp.can_fetch('*', target_url)
    except urllib.error.URLError as e:
        print(f"Error fetching {robots_url}: {e}")
        return False

    rp.parse(data.splitlines())
    return rp.can_fetch('*', target_url)

# Main function
def scrape_data(url):
    print(f"Scraping data from {url}")

    if not is_scraping_allowed(url):
        print("Scraping is not allowed for this website. Exiting.")
        exit_program()

    soup = get_soup(url)

    try:
        composers_script_tag = soup.find("script", string=re.compile("catpagejs"))
        composers_script_str = str(composers_script_tag)
        composers_pattern = re.compile(r'catpagejs,{"s1":(.*?)}\);')
        composers_match = composers_pattern.search(composers_script_str)
        composers_data_str = composers_match.group(1)
        composers_data = json.loads(composers_data_str)

        exclude_names=["collections", "various", "traditional"]

        composer_link_base = f"{MAIN_URL}{CATEGORY_BASE}"

        if not is_scraping_allowed(composer_link_base):
            print("Scraping is not allowed for composers. Exiting.")
            exit_program()

        for composer_letter, composers in composers_data.items():
            for composer_full_name in composers:

                if any(exclude_name.lower() in composer_full_name.lower() for exclude_name in exclude_names):
                    print(f"Skipping composer: {composer_full_name} (Excluded)")
                    continue

                if composer_is_processed(composer_full_name):
                    print(f"Skipping composer: {composer_full_name} (Already Processed)")
                    continue

                print(f"Processing composer: {composer_full_name}")

                composer_link = composer_link_base + quote(composer_full_name.replace(" ", "_"))

                try:
                    process_composer(composer_full_name, composer_link)

                except Exception as comp_err:
                    print(f"Error processing composer {composer_full_name}: {comp_err}")
                    pass

                with conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE Composers SET processed = 1, updated_at = CURRENT_TIMESTAMP WHERE full_name = ?", (composer_full_name,))
            
    except Exception as err:
        print(f"Error scraping data from {url}: {err}")

    finally:
        conn.close()

# Main execution
create_database()
scrape_data(START_URL)