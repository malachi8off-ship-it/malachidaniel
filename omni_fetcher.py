import os
import requests
import re
from bs4 import BeautifulSoup
from ddgs import DDGS
from google import genai
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'raw_lyrics')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def fix_spelling_with_ai(title, artist):
    """Uses AI to standardize typos and Hinglish/Manglish transliteration spellings."""
    prompt = (
        f"Correct the spelling, typos, and transliteration for the worship song titled '{title}' by '{artist}'. "
        f"Return the exact standard official song title and artist name. "
        f"Format your response as EXACTLY: 'TITLE | ARTIST' with no extra words."
    )
    
    if gemini_client:
        try:
            res = gemini_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            if res.text and '|' in res.text:
                parts = res.text.strip().split('|')
                return parts[0].strip(), parts[1].strip()
        except Exception:
            pass

    if groq_client:
        try:
            res = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            text = res.choices[0].message.content.strip()
            if '|' in text:
                parts = text.split('|')
                return parts[0].strip(), parts[1].strip()
        except Exception:
            pass

    return title, artist

def fetch_from_lrclib(title, artist):
    """Attempt 1 & 2: Searches LRCLIB API for lyrics."""
    url = f"https://lrclib.net/api/search?q={title} {artist}"
    try:
        headers = {'User-Agent': 'MalachiDanielBot/2.0 (malachidaniel.com)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            for track in results:
                if track.get('plainLyrics'):
                    return track['plainLyrics'], track['trackName'], track['artistName']
    except Exception as e:
        print(f"❌ Connection error (LRCLIB): {e}")
    return None, None, None

def fetch_via_ddg_scraper(title, artist):
    """Attempt 3: Pure-Python Web Scraper using DuckDuckGo Search + BeautifulSoup."""
    print(f"🌐 Searching web (Pure Python) for '{title}' by '{artist}'...")
    query = f"{title} {artist} lyrics"
    
    try:
        results = []
        # Use the updated DDGS context manager syntax
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(r)
                
        if not results:
            print("❌ No search engine results returned.")
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        for item in results:
            target_url = item.get('href')
            if not target_url:
                continue

            print(f"🔗 Checking: {target_url}")
            try:
                page_resp = requests.get(target_url, headers=headers, timeout=8)
                if page_resp.status_code != 200:
                    continue

                page_soup = BeautifulSoup(page_resp.text, 'html.parser')

                # Strip irrelevant HTML noise
                for tag in page_soup(["script", "style", "nav", "header", "footer", "form"]):
                    tag.extract()

                lyrics_text = ""

                # Target common lyric containers or post content blocks
                for container in page_soup.find_all(['div', 'section', 'article', 'pre']):
                    class_or_id = (" ".join(container.get('class', [])) + " " + str(container.get('id', ''))).lower()
                    if any(kw in class_or_id for kw in ['lyric', 'song-text', 'entry-content', 'post-content', 'verse']):
                        # Use a more robust extraction method that preserves line breaks
                        text = "\n".join([line.strip() for line in container.get_text(separator='\n').splitlines() if line.strip()])
                        if len(text) > 100:
                            lyrics_text = text
                            break

                # Fallback check for general text blocks with multiple lines if specific containers aren't found
                if not lyrics_text:
                    for div in page_soup.find_all('div'):
                        text = "\n".join([line.strip() for line in div.get_text(separator='\n').splitlines() if line.strip()])
                        if len(text) > 150 and '\n' in text and "cookie" not in text.lower() and "privacy" not in text.lower():
                            lyrics_text = text
                            break

                if lyrics_text and len(lyrics_text) > 50:
                    print("✅ Successfully scraped lyrics!")
                    return lyrics_text.strip()

            except Exception:
                continue

        print("⚠️ Checked search results, but could not isolate lyrics content.")
        return None

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return None

def save_lyrics(title, artist, lyrics):
    filename = f"{slugify(title)}-{slugify(artist)}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"{title}\n")
        f.write(f"{artist}\n")
        f.write(f"{lyrics}\n")
        
    print(f"💾 Successfully saved to {filepath}")

def main():
    print("========================================")
    print("   OMNI-FETCHER: WATERFALL LYRICS BOT  ")
    print("========================================")
    
    while True:
        print("\n(Type 'quit' or 'exit' to stop)")
        raw_title = input("Enter Song Title: ").strip()
        if raw_title.lower() in ['quit', 'exit']:
            break
            
        raw_artist = input("Enter Artist Name: ").strip()
        if raw_artist.lower() in ['quit', 'exit']:
            break
            
        # STEP 1: Direct API Search
        print(f"\n🔍 Searching LRCLIB for '{raw_title}' by '{raw_artist}'...")
        lyrics, actual_title, actual_artist = fetch_from_lrclib(raw_title, raw_artist)
        
        corrected_title, corrected_artist = raw_title, raw_artist

        # STEP 2: AI Correction + API Search
        if not lyrics:
            print("⚠️ Direct search failed. Running AI spell & transliteration correction...")
            corrected_title, corrected_artist = fix_spelling_with_ai(raw_title, raw_artist)
            
            if corrected_title != raw_title or corrected_artist != raw_artist:
                print(f"✨ Corrected Query to: '{corrected_title}' by '{corrected_artist}'")
                print(f"🔍 Re-searching LRCLIB with corrected query...")
                lyrics, actual_title, actual_artist = fetch_from_lrclib(corrected_title, corrected_artist)

        # STEP 3: Pure-Python Web Scraper Fallback
        if not lyrics:
            print("⚠️ API returned no lyrics. Switching to Pure-Python Web Scraper...")
            scraped_lyrics = fetch_via_ddg_scraper(corrected_title, corrected_artist)
            if scraped_lyrics:
                lyrics = scraped_lyrics
                actual_title = corrected_title
                actual_artist = corrected_artist

        # SAVE RESULT
        if lyrics:
            save_title = actual_title if actual_title else raw_title
            save_artist = actual_artist if actual_artist else raw_artist
            print(f"🎉 Success! Got lyrics for: {save_title} by {save_artist}")
            save_lyrics(save_title, save_artist, lyrics)
        else:
            print(f"❌ All fallback methods failed for '{raw_title}'.")

if __name__ == "__main__":
    main()