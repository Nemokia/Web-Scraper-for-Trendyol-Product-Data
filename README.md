# Web Scraper for Trendyol Product Data

## Overview
This project is a Python-based web scraper designed to extract product data from Trendyol dynamically loaded pages. The scraper collects information such as product links, brands, names, prices, and color variants while providing options for filtering based on price and brand. The extracted data is saved in text and Excel files for easy accessibility.

## Features
- Dynamic loading support for pages with infinite scroll.
- Product filtering by:
  - Minimum price
  - Maximum price
  - Brand name
- Prevention of duplicate product link storage.
- Data saved in:
  - Text files (product links only).
  - Excel files (detailed product information).
- Batch scraping to manage large datasets efficiently.
- User-defined filter settings for flexible scraping.

## Requirements
The following Python libraries are required:
- `selenium`
- `webdriver_manager`
- `pandas`
- `datetime`
- `time`

Install the dependencies using pip:
```bash
pip install selenium webdriver-manager pandas
```

## Setup Instructions
1. Install Google Chrome and ensure it is up-to-date.
2. Install ChromeDriver using the `webdriver_manager` library.
3. Clone this repository and navigate to the project directory.

## Usage
### Configuration
- Configure ChromeDriver options in the script for headless or GUI mode.
- Replace the `base_url` variable with the desired Trendyol page URL.

### Running the Script
Run the script in a terminal or IDE:
```bash
python scraper.py
```
The script will prompt you to enter optional filters:
- **Minimum Price**: Enter a numeric value or leave blank for no filter.
- **Maximum Price**: Enter a numeric value or leave blank for no filter.
- **Brand Name**: Enter a brand name or leave blank for no filter.

### Output
- **Text File**: Contains product links, named after the product group.
- **Excel File**: Contains detailed product data, named after the product group and current date.

## Script Details
### Functions
#### `sanitize_filename(filename)`
Removes invalid characters from filenames to ensure compatibility.

#### `filter_products(products, min_price, max_price, brand_name)`
Filters products based on user-defined criteria.

#### `read_existing_links(group_title)`
Reads previously saved product links from the corresponding text file to avoid duplication.

#### `save_data_to_files(group_title, data, current_date, existing_links)`
Saves product links and details into separate files, avoiding duplicates.

#### `save_filtered_data_to_files(group_title, filter_type, filter_value, data, current_date)`
Saves filtered product data into new files with descriptive filenames.

#### `scrape_pages_in_batches(driver, base_url, group_title, current_date, min_price, max_price, brand_name, existing_links, max_idle_attempts)`
Handles the scraping process in batches, manages infinite scrolling, and applies filters.

### ChromeDriver Configuration
The script uses the following Chrome options:
- `--headless`: Run Chrome without a GUI.
- `--disable-web-security`: Allows handling mixed content.
- `--disable-gpu`: Optimizes performance in headless mode.

You can modify these settings in the `options` section of the script.

## Example
1. Set the `base_url` to the Trendyol category you wish to scrape (e.g., men's shorts).
2. Run the script:
   ```
   python scraper.py
   ```
3. Enter filters when prompted (or leave blank for no filters):
   ```
   Minimum Price: 100
   Maximum Price: 500
   Brand Name: Nike
   ```
4. Check the output files for results:
   - `erkek-sort.txt`: Contains all product links.
   - `erkek-sort_2024-12-11.xlsx`: Contains product details filtered by the specified criteria.

## Notes
- Ensure a stable internet connection to handle dynamic page loading.
- Adjust the `max_idle_attempts` parameter for more or fewer attempts at scraping new products when no changes are detected.
