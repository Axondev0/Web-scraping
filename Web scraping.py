import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime


def scrape_website(url):
    """
    Scrapes ALL information from a given URL with NO limits

    Args:
        url (str): The website URL to scrape

    Returns:
        dict: Dictionary containing ALL scraped data
    """

    try:
        # Send a GET request to the URL
        # The headers make the request look like it's coming from a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)

        # Check if the request was successful (status code 200)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract ALL information from the webpage
        data = {
            'url': url,
            'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title': '',
            'headings': [],
            'paragraphs': [],
            'links': [],
            'images': [],
            'meta_tags': [],
            'all_text': '',
            'scripts': [],
            'styles': []
        }

        # Get the page title
        if soup.title:
            data['title'] = soup.title.string.strip()

        # Get ALL headings (h1, h2, h3, h4, h5, h6) - NO LIMIT
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            data['headings'].append({
                'tag': heading.name,
                'text': heading.get_text().strip()
            })

        # Get ALL paragraphs - NO LIMIT
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if text:  # Only add non-empty paragraphs
                data['paragraphs'].append(text)

        # Get ALL links - NO LIMIT
        links = soup.find_all('a', href=True)
        for link in links:
            data['links'].append({
                'text': link.get_text().strip(),
                'url': link['href']
            })

        # Get ALL images - NO LIMIT
        images = soup.find_all('img')
        for img in images:
            data['images'].append({
                'src': img.get('src', ''),
                'alt': img.get('alt', 'No alt text'),
                'title': img.get('title', '')
            })

        # Get ALL meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            meta_data = {}
            for attr in ['name', 'property', 'content', 'charset', 'http-equiv']:
                if meta.get(attr):
                    meta_data[attr] = meta.get(attr)
            if meta_data:
                data['meta_tags'].append(meta_data)

        # Get all visible text from the page
        data['all_text'] = soup.get_text(separator=' ', strip=True)

        # Get all script tags content
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                data['scripts'].append(script.string.strip())

        # Get all style tags content
        styles = soup.find_all('style')
        for style in styles:
            if style.string:
                data['styles'].append(style.string.strip())

        # Add statistics
        data['statistics'] = {
            'total_headings': len(data['headings']),
            'total_paragraphs': len(data['paragraphs']),
            'total_links': len(data['links']),
            'total_images': len(data['images']),
            'total_meta_tags': len(data['meta_tags']),
            'total_scripts': len(data['scripts']),
            'total_styles': len(data['styles']),
            'total_text_length': len(data['all_text'])
        }

        return data

    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        return {'error': f'Failed to scrape {url}: {str(e)}'}

    except Exception as e:
        # Handle any other errors
        return {'error': f'An error occurred: {str(e)}'}


def save_to_file(data, base_filename='(given name)_scraped'):
    """
    Saves ALL scraped data to both JSON and Excel (XLSX) files

    Args:
        data (dict): The data to save
        base_filename (str): Base name for the output files (without extension)
    """
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"{base_filename}_{timestamp}.json"
    xlsx_filename = f"{base_filename}_{timestamp}.xlsx"

    # Save as JSON - This includes EVERYTHING
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✓ Complete data saved to {json_filename}")

    # Save as Excel (XLSX) - Organized in multiple sheets
    with pd.ExcelWriter(xlsx_filename, engine='openpyxl') as writer:

        # Sheet 1: Statistics Summary
        if 'statistics' in data:
            stats_df = pd.DataFrame(
                list(data['statistics'].items()), columns=['Metric', 'Count'])
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)

        # Sheet 2: Basic Information
        basic_info = pd.DataFrame({
            'Field': ['URL', 'Scrape Date', 'Title'],
            'Value': [data['url'], data.get('scrape_date', ''), data['title']]
        })
        basic_info.to_excel(writer, sheet_name='Basic Info', index=False)

        # Sheet 3: ALL Headings
        if data['headings']:
            headings_df = pd.DataFrame(data['headings'])
            headings_df.insert(0, 'Number', range(
                1, len(data['headings']) + 1))
            headings_df.to_excel(writer, sheet_name='Headings', index=False)

        # Sheet 4: ALL Paragraphs
        if data['paragraphs']:
            paragraphs_df = pd.DataFrame({
                'Paragraph Number': range(1, len(data['paragraphs']) + 1),
                'Text': data['paragraphs']
            })
            paragraphs_df.to_excel(
                writer, sheet_name='Paragraphs', index=False)

        # Sheet 5: ALL Links
        if data['links']:
            links_df = pd.DataFrame(data['links'])
            links_df.insert(0, 'Number', range(1, len(data['links']) + 1))
            links_df.to_excel(writer, sheet_name='Links', index=False)

        # Sheet 6: ALL Images
        if data['images']:
            images_df = pd.DataFrame(data['images'])
            images_df.insert(0, 'Number', range(1, len(data['images']) + 1))
            images_df.to_excel(writer, sheet_name='Images', index=False)

        # Sheet 7: ALL Meta Tags
        if data['meta_tags']:
            meta_df = pd.DataFrame(data['meta_tags'])
            meta_df.to_excel(writer, sheet_name='Meta Tags', index=False)

        # Sheet 8: Complete Text Content
        if data.get('all_text'):
            text_df = pd.DataFrame({
                'Complete Page Text': [data['all_text']]
            })
            text_df.to_excel(writer, sheet_name='All Text', index=False)

    print(f"✓ Complete data saved to {xlsx_filename}")
    print(f"\n{'='*60}")
    print("Both files saved successfully with ALL scraped content!")
    print(f"{'='*60}")


def main():
    """
    Main function that scrapes (website link provided in the prompt) with NO LIMITS
    """
    # URL is hardcoded - (website link provided in the prompt)
    url = "(website link provided in the prompt)"

    print("=" * 60)
    print("UNLIMITED WEB SCRAPER - (website link provided in the prompt)")
    print("=" * 60)
    print(f"\nTarget URL: {url}")
    print("Scraping ALL content with NO LIMITS...")
    print("\nThis may take a moment...\n")

    # Perform the scraping
    result = scrape_website(url)

    # Check if there was an error
    if 'error' in result:
        print(f"\n❌ ERROR: {result['error']}")
        return

    # Display results
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    print(f"\n Title: {result['title']}")
    print(f" Scraped on: {result['scrape_date']}")

    print("\n" + "-" * 60)
    print("STATISTICS:")
    print("-" * 60)

    stats = result.get('statistics', {})
    print(f"✓ Total Headings: {stats.get('total_headings', 0)}")
    print(f"✓ Total Paragraphs: {stats.get('total_paragraphs', 0)}")
    print(f"✓ Total Links: {stats.get('total_links', 0)}")
    print(f"✓ Total Images: {stats.get('total_images', 0)}")
    print(f"✓ Total Meta Tags: {stats.get('total_meta_tags', 0)}")
    print(f"✓ Total Scripts: {stats.get('total_scripts', 0)}")
    print(f"✓ Total Styles: {stats.get('total_styles', 0)}")
    print(
        f"✓ Total Text Length: {stats.get('total_text_length', 0):,} characters")

    # Automatically save the data
    print("\n" + "=" * 60)
    print("SAVING ALL DATA...")
    print("=" * 60 + "\n")

    save_to_file(result)

    print("\n Scraping and saving complete!")
    print("\nFiles created:")
    print("  1. JSON file - Contains ALL raw data")
    print("  2. XLSX file - Contains organized data in multiple sheets")
    print("\n" + "=" * 60)


# Run the program automatically
if __name__ == "__main__":
    main()
