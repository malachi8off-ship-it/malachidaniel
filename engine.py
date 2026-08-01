import requests
import lyricsgenius
import os
import re
from dotenv import load_dotenv

load_dotenv()

GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
TARGET_FOLDER = "raw_lyrics"

genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.remove_section_headers = True

def normalize_string(text):
    """Strips all spaces, underscores, and non-alphanumeric characters for clean checks."""
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_").lower()

def clean_genius_artifacts(text):
    text = re.sub(r'\d+Embed$', '', text)
    text = re.sub(r'Embed$', '', text)
    return text.strip()

def get_existing_songs():
    """Scans raw_lyrics folder for existing titles."""
    if not os.path.exists(TARGET_FOLDER):
        os.makedirs(TARGET_FOLDER)
    existing_files = os.listdir(TARGET_FOLDER)
    return [normalize_string(os.path.splitext(f)[0]) for f in existing_files]

def fetch_and_save_lyrics(song_title, artist):
    try:
        song = genius.search_song(song_title, artist)

        if song:
            if artist.lower() in song.artist.lower():
                if not os.path.exists(TARGET_FOLDER):
                    os.makedirs(TARGET_FOLDER)
                
                filename = os.path.join(TARGET_FOLDER, f"{clean_filename(song.title)}.txt")
                clean_lyrics = clean_genius_artifacts(song.lyrics)

                file_content = f"{song.title}\n{song.artist}\nlyrics\n{clean_lyrics}"

                with open(filename, "w", encoding="utf-8") as file:
                    file.write(file_content)
                
                print(f"✅ Success! Saved to: {filename}\n")
            else:
                print(f"⏭️ Skipped: Genius returned '{song.artist}' instead of '{artist}'\n")
        else:
            print("❌ Song not found on Genius.\n")
            
    except Exception as e:
        print(f"⚠️ An error occurred during fetching: {e}\n")

def run_engine():
    print("🔄 Connecting to iTunes Top Charts (Christian & Gospel)...")
    
    url = "https://itunes.apple.com/us/rss/topsongs/limit=50/genre=22/json"
    
    try:
        response = requests.get(url)
        data = response.json()
        songs = data.get("feed", {}).get("entry", [])
    except Exception as e:
        print(f"⚠️ Could not connect to iTunes: {e}")
        return

    existing_songs = get_existing_songs()
    print(f"✅ Found {len(songs)} trending songs in iTunes charts!\n")

    for item in songs:
        title = item.get("im:name", {}).get("label", "Unknown Title")
        artist = item.get("im:artist", {}).get("label", "Unknown Artist")
        
        # Check if the song is already downloaded
        norm_title = normalize_string(title)
        if any(norm_title in existing for existing in existing_songs):
            print(f"⏩ [Already Archived] Skipping: {title} by {artist}")
            continue

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
            # Add to local list so duplicate check works within the same session
            existing_songs.append(norm_title)
        else:
            print("⏭️ Skipped.\n")
            
if __name__ == "__main__":
    run_engine()