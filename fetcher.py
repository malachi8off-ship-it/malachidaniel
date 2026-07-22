import lyricsgenius
import os
import re

GENIUS_TOKEN = "1KWejaYTRDJQYA5urhnH27-bavYEWLIvHv0tMbabGccOSXT11q9Mj3TxEnhXJFNE"  # Keep your working token here
genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.remove_section_headers = True 

# 1. CHANGE THIS to the exact folder name where your generator.py looks for files
TARGET_FOLDER = "raw_lyrics" 

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_").lower()

def clean_genius_artifacts(text):
    """Removes the annoying 'Embed' numbers Genius adds to the very end"""
    text = re.sub(r'\d+Embed$', '', text)
    text = re.sub(r'Embed$', '', text)
    return text.strip()

def fetch_and_save_lyrics():
    print("🎵 --- Lyric Fetcher (Clean Format) --- 🎵")
    artist = input("Enter Artist Name: ")
    song_title = input("Enter Song Title: ")

    try:
        song = genius.search_song(song_title, artist)
        
        if song:
            # Ensure the target folder exists so it doesn't save to the main folder
            if not os.path.exists(TARGET_FOLDER):
                os.makedirs(TARGET_FOLDER)
                
            filename = os.path.join(TARGET_FOLDER, f"{clean_filename(song.title)}.txt")
            
            # Clean up the lyrics text body
            clean_lyrics = clean_genius_artifacts(song.lyrics)
            
            # Exact clean format: No "Title:", "Artist:", "Category:", or lines of dashes
            file_content = f"{song.title}\n"       # Line 1: Just the title
            file_content += f"{song.artist}\n"     # Line 2: Just the artist name
            file_content += "lyrics\n"             # Line 3: Just the category type
            file_content += clean_lyrics           # Line 4+: The lyrics themselves
            
            with open(filename, "w", encoding="utf-8") as file:
                file.write(file_content)
                
            print(f"\n✅ Success! Saved to: {filename}")
        else:
            print("\n❌ Song not found.")
            
    except Exception as e:
        print(f"\n⚠️ An error occurred: {e}")

if __name__ == "__main__":
    fetch_and_save_lyrics()