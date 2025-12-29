from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import time
import os
import requests

# Configuration
USERNAME = "Jin67171"
MAX_TWEETS = 50
SCROLL_PAUSE_TIME = 4  # Increased again
DOWNLOAD_IMAGES = True

# Create images folder
if DOWNLOAD_IMAGES:
    img_folder = f"twitter_images_{USERNAME}"
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    print(f"Images will be saved to: {img_folder}/")

print(f"Starting Twitter scraper for @{USERNAME}...")
print("Opening Chrome browser...")

# Setup Chrome driver
options = webdriver.ChromeOptions()
# Removed headless - browser will be visible
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)

try:
    # Navigate to profile
    url = f"https://twitter.com/{USERNAME}"
    driver.get(url)
    print(f"Loaded profile: {url}")
    print("Waiting for page to fully load...")

    # Longer wait for page load
    time.sleep(8)  # Increased from 5

    # Scroll a bit to trigger loading
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)

    tweets_data = []
    seen_tweets = set()
    scroll_attempts = 0
    max_scrolls = 40  # Increased more
    no_new_tweets_count = 0  # Track if we're getting new tweets

    print("\nScraping tweets...")

    while len(tweets_data) < MAX_TWEETS and scroll_attempts < max_scrolls:
        # Store count before scraping
        prev_count = len(tweets_data)

        # Find all tweet articles
        tweet_elements = driver.find_elements(
            By.XPATH, '//article[@data-testid="tweet"]')

        for tweet_elem in tweet_elements:
            if len(tweets_data) >= MAX_TWEETS:
                break

            try:
                # Extract tweet text
                try:
                    text_elem = tweet_elem.find_element(
                        By.XPATH, './/div[@data-testid="tweetText"]')
                    tweet_text = text_elem.text
                except:
                    tweet_text = "No text"

                # Extract date/time
                try:
                    time_elem = tweet_elem.find_element(By.XPATH, './/time')
                    tweet_date = time_elem.get_attribute('datetime')
                except:
                    tweet_date = "Unknown"

                # Extract engagement metrics
                try:
                    reply_elem = tweet_elem.find_element(
                        By.XPATH, './/button[@data-testid="reply"]//span')
                    replies = reply_elem.text if reply_elem.text else "0"
                except:
                    replies = "0"

                try:
                    retweet_elem = tweet_elem.find_element(
                        By.XPATH, './/button[@data-testid="retweet"]//span')
                    retweets = retweet_elem.text if retweet_elem.text else "0"
                except:
                    retweets = "0"

                try:
                    like_elem = tweet_elem.find_element(
                        By.XPATH, './/button[@data-testid="like"]//span')
                    likes = like_elem.text if like_elem.text else "0"
                except:
                    likes = "0"

                # Extract images
                image_urls = []
                downloaded_images = []
                try:
                    img_elements = tweet_elem.find_elements(
                        By.XPATH, './/img[contains(@src, "pbs.twimg.com/media")]')
                    for idx, img in enumerate(img_elements):
                        img_url = img.get_attribute('src')
                        # Convert to high quality
                        img_url = img_url.replace('&name=small', '&name=large')
                        image_urls.append(img_url)

                        # Download image
                        if DOWNLOAD_IMAGES:
                            try:
                                img_name = f"{USERNAME}_tweet{len(tweets_data)+1}_img{idx+1}.jpg"
                                img_path = os.path.join(img_folder, img_name)
                                img_data = requests.get(
                                    img_url, timeout=10).content
                                with open(img_path, 'wb') as f:
                                    f.write(img_data)
                                downloaded_images.append(img_name)
                            except:
                                pass
                except:
                    pass

                # Create unique ID to avoid duplicates
                tweet_id = f"{tweet_text[:50]}_{tweet_date}"

                if tweet_id not in seen_tweets:
                    seen_tweets.add(tweet_id)
                    tweets_data.append({
                        'date': tweet_date,
                        'username': USERNAME,
                        'tweet_text': tweet_text,
                        'replies': replies,
                        'retweets': retweets,
                        'likes': likes,
                        'image_urls': ', '.join(image_urls) if image_urls else 'No images',
                        'images_count': len(image_urls),
                        'downloaded_images': ', '.join(downloaded_images) if downloaded_images else 'No images'
                    })

                    if len(tweets_data) % 10 == 0:
                        print(f"Scraped {len(tweets_data)} tweets...")

            except Exception as e:
                continue

        # Scroll down to load more tweets
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        scroll_attempts += 1

        # Check if we got new tweets
        if len(tweets_data) == prev_count:
            no_new_tweets_count += 1
            # Scroll more aggressively
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            if no_new_tweets_count >= 5:  # Stop if no new tweets after 5 scrolls
                print("No new tweets found after multiple attempts. Stopping...")
                break
        else:
            no_new_tweets_count = 0  # Reset counter

    # Create DataFrame and save
    df = pd.DataFrame(tweets_data)

    filename = f'twitter_{USERNAME}_{len(tweets_data)}tweets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')

    print(f"\n✓ Successfully scraped {len(tweets_data)} tweets!")
    print(f"✓ Saved to: {filename}")
    if DOWNLOAD_IMAGES:
        total_images = sum(1 for t in tweets_data if t['images_count'] > 0)
        print(
            f"✓ Downloaded images from {total_images} tweets to: {img_folder}/")

    # Show preview
    print("\n--- PREVIEW (First 3 tweets) ---")
    for idx, row in df.head(3).iterrows():
        print(f"\nTweet {idx + 1}:")
        print(f"Date: {row['date']}")
        print(f"Text: {row['tweet_text'][:100]}...")
        print(f"Engagement: {row['likes']} likes, {row['retweets']} retweets")
        print(f"Images: {row['images_count']}")

except Exception as e:
    print(f"\n✗ Error: {str(e)}")

finally:
    driver.quit()
    print("\nBrowser closed.")
