import os
import io  
import requests
from serpapi import GoogleSearch
from PIL import Image, UnidentifiedImageError
import pytesseract
import urllib3
import sqlite3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Database setup
""" Initializes the SQLite database and creates a table named menu_items if it doesn't exist.
This table has columns for id, item_name, and price. """
def init_db():
    conn = sqlite3.connect('menu_items.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY,
            item_name TEXT,
            price TEXT
        )
    ''')
    conn.commit()
    return conn, cursor


""" Performs a Google image search for restaurant menus in Mumbai using the SerpAPI. 
It downloads each image and saves it locally if it is valid. """

def scrape_google_menu_images(query, api_key):
    params = {
        "engine": "google",  # Ensure we use the correct engine
        "q": query,
        "tbm": "isch",
        "gl": "in",  # Adjust the geolocation parameter if needed
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    image_results = results.get('images_results', [])

    if not os.path.exists('menu_images'):
        os.makedirs('menu_images')

    image_urls = []
    for idx, image in enumerate(image_results):
        img_url = image['original']
        img_data = requests.get(img_url, verify=False).content
        with open(f'menu_images/menu_{idx}.jpg', 'wb') as handler:
            handler.write(img_data)
        image_urls.append(f'menu_images/menu_{idx}.jpg')

    return image_urls

""" Opens an image and uses pytesseract to extract text from it. 
Handles errors that occur if the image is not identified or any other exception occurs. """

def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"Failed to process image {image_path}: {e}")
        return ""

""" Parses the OCR text to extract item names and prices. """    

def extract_items_and_prices(ocr_text):
    lines = ocr_text.split('\n')
    items_prices = []
    for line in lines:
        parts = line.split()
        if len(parts) > 1:
            item = ' '.join(parts[:-1])
            price = parts[-1]
            items_prices.append((item, price))
    return items_prices

""" Inserts the extracted items and prices into the SQLite database. """
# Store in Database
def store_items_in_db(cursor, items_prices):
    for item, price in items_prices:
        cursor.execute('INSERT INTO menu_items (item_name, price) VALUES (?, ?)', (item, price))






# Main function
def main():
    api_key = 'f3d7ebfa1ed4f8cc79f1e782c2c14d58a6aa60e0c685d955fe16bf5fb0394fb2'  # Replace with your actual SerpAPI key
    query = 'restaurant menu Mumbai'

    conn, cursor = init_db()

    menu_images = scrape_google_menu_images(query, api_key)
    for image_path in menu_images:
        ocr_text = ocr_image(image_path)
        items_prices = extract_items_and_prices(ocr_text)
        store_items_in_db(cursor, items_prices)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()