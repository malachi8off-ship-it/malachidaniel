import os
import re
from dotenv import load_dotenv
import lyricsgenius

load_dotenv()
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')

if not GENIUS_TOKEN:
    print("❌ Error: GENIUS_TOKEN not found in .env file.")
    exit()

genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.verbose = False

RAW_LYRICS_DIR = 'raw_lyrics'

def normalize_string(text):
    """Strips all spaces, underscores, and punctuation for strict title matching."""
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def get_existing_songs():
    """Scans raw_lyrics and returns a list of normalized song identifiers."""
    if not os.path.exists(RAW_LYRICS_DIR):
        os.makedirs(RAW_LYRICS_DIR)
    
    existing_files = os.listdir(RAW_LYRICS_DIR)
    # Strip extensions and normalize filenames (e.g., 'trust_in_god.txt' -> 'trustingod')
    return [normalize_string(os.path.splitext(f)[0]) for f in existing_files]

def main():
    existing_songs = get_existing_songs()
    
    print("\n🎵 Christian LyricsHub - Song Discovery Engine 🎵")
    print("-" * 50)
    artist_name = input("Enter a Christian artist to search for: ")
    
    print(f"\n🔍 Searching Genius for top songs by {artist_name}...")
    try:
        artist = genius.search_artist(artist_name, max_songs=15, sort="popularity")
    except Exception as e:
        print(f"❌ Error fetching artist: {e}")
        return
    
    if not artist:
        print("❌ Artist not found on Genius.")
        return

    # Filter out songs using normalized comparison
    recommended_songs = []
    for song in artist.songs:
        norm_title = normalize_string(song.title)
        
        # Check if normalized title exists anywhere in existing filenames
        is_existing = any(norm_title in existing for existing in existing_songs)
        
        if not is_existing:
            recommended_songs.append(song)

    if not recommended_songs:
        print("\n✅ You already have all the top songs for this artist in your archive!")
        return

    print(f"\n✨ Found {len(recommended_songs)} new songs:")
    for i, song in enumerate(recommended_songs, 1):
        print(f"  {i}. {song.title}")

    print("\n" + "="*50)
    print("Review: 'y' to add, 'n' to skip, 'q' to quit.")
    print("="*50 + "\n")
    
    for song in recommended_songs:
        choice = input(f"Add '{song.title}'? (y/n/q): ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'y':
            safe_title = re.sub(r'[\\/*?:"<>|]', "", song.title).replace(" ", "_").lower()
            filename = os.path.join(RAW_LYRICS_DIR, f"{safe_title}.txt")
            
            clean_lyrics = re.sub(r'\d+Embed$', '', song.lyrics)
            clean_lyrics = re.sub(r'Embed$', '', clean_lyrics).strip()
            
            file_content = f"{song.title}\n{artist.name}\nlyrics\n{clean_lyrics}"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
            print(f"  ✅ Saved to {filename}\n")
        else:
            print("  ⏭️ Skipped.\n")

if __name__ == "__main__":
    main()