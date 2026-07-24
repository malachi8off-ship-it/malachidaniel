import requests
import lyricsgenius
import os
import re
from dotenv import load_dotenv

# Load the hidden environment variables
load_dotenv()

# Pull the token securely from the .env file
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
TARGET_FOLDER = "raw_lyrics"

genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.remove_section_headers = True

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_").lower()

def clean_genius_artifacts(text):
    text = re.sub(r'\d+Embed$', '', text)
    text = re.sub(r'Embed$', '', text)
    return text.strip()

def fetch_and_save_lyrics(song_title, artist):
    try:
        # Search Genius for the approved song
        song = genius.search_song(song_title, artist)
        
        if song:
            if not os.path.exists(TARGET_FOLDER):
                os.makedirs(TARGET_FOLDER)
                
            filename = os.path.join(TARGET_FOLDER, f"{clean_filename(song.title)}.txt")
            clean_lyrics = clean_genius_artifacts(song.lyrics)
            
            # Save exactly how your generator.py expects it
            file_content = f"{song.title}\n{song.artist}\nlyrics\n{clean_lyrics}"
            
            with open(filename, "w", encoding="utf-8") as file:
                file.write(file_content)
                
            print(f"✅ Success! Saved to: {filename}\n")
        else:
            print(f"❌ Song not found on Genius. Skipping...\n")
            
    except Exception as e:
        print(f"⚠️ An error occurred during fetching: {e}\n")

def run_engine():
    print("🔄 Connecting to iTunes Top Charts (Christian & Gospel)...")
    
    # Using the iTunes Top 50 Charts specifically for Genre 22 (Christian & Gospel)
    url = "https://itunes.apple.com/us/rss/topsongs/limit=50/genre=22/json"
    
    try:
        response = requests.get(url)
        data = response.json()
        # The Top Charts RSS feed structures its JSON differently
        songs = data.get("feed", {}).get("entry", [])
    except Exception as e:
        print(f"⚠️ Could not connect to iTunes: {e}")
        return

    print(f"✅ Found {len(songs)} trending songs! Let's review them.\n")

    for item in songs:
        # Extracting the title and artist from the RSS format
        title = item.get("im:name", {}).get("label", "Unknown Title")
        artist = item.get("im:artist", {}).get("label", "Unknown Artist")
        
        print("-" * 40)
        print(f"🎵 Title:  {title}")
        print(f"🎤 Artist: {artist}")
        
        choice = input("Fetch this song? (y = yes / n = skip / q = quit): ").strip().lower()
        
        if choice == 'q':
            print("\n🛑 Stopping the engine. Goodbye!")
            break
        elif choice == 'y':
            print("⏳ Fetching lyrics from Genius...")
            fetch_and_save_lyrics(title, artist)
        else:
            print("⏭️ Skipped.\n")
            
if __name__ == "__main__":
    run_engine()