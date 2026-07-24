import os
import re
import lyricsgenius
from dotenv import load_dotenv

# Load the hidden environment variables
load_dotenv()
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")
TARGET_FOLDER = "raw_lyrics"

# Initialize Genius
genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.remove_section_headers = True  # Keeps the lyrics clean

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_").lower()

def clean_genius_artifacts(text):
    text = re.sub(r'\d+Embed$', '', text)
    text = re.sub(r'Embed$', '', text)
    return text.strip()

def get_lyrics_preview(lyrics, num_lines=4):
    # Split the lyrics into lines and remove any empty blank lines
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    # Grab just the first 'num_lines'
    return "\n".join(lines[:num_lines])

def run_interactive_engine():
    print("\n=== 🎵 Advanced Manual Lyrics Fetcher ===")
    print("Type 'q' at the search prompt to quit the app.\n")
    
    while True:
        # --- OUTER LOOP: The Search Prompt ---
        query = input("\n🔍 Enter a song title (or 'q' to quit): ").strip()
        
        if query.lower() == 'q':
            print("Exiting engine...")
            break
            
        if not query:
            continue
            
        print(f"⏳ Searching Genius for '{query}'...")
        
        # Pull a list of search results instead of just the top hit
        search_results = genius.search_songs(query)
        
        # Check if the search returned any hits
        if not search_results or not search_results.get('hits'):
            print(f"❌ Couldn't find anything matching '{query}'.")
            continue
            
        hits = search_results['hits']
        
        while True:
            # --- INNER LOOP: The Result List ---
            print(f"\n=== 📋 Search Results for '{query}' ===")
            for i, hit in enumerate(hits):
                title = hit['result']['title']
                artist = hit['result']['primary_artist']['name']
                print(f"[{i + 1}] {title} by {artist}")
            
            print("-" * 45)
            print("[b] Back to new search")
            print("=" * 45)
            
            choice = input("\nEnter song number to view (or 'b' to go back): ").strip().lower()
            
            if choice == 'b' or choice == 'q':
                break # Breaks the inner loop, taking you back to the search prompt
            
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(hits):
                print("⚠️ Invalid choice. Please enter a valid number from the list.")
                continue
                
            # Get the ID of the chosen song
            selected_index = int(choice) - 1
            selected_hit = hits[selected_index]['result']
            
            print(f"\n⏳ Fetching lyrics for '{selected_hit['title']}'...")
            
            # Fetch the actual lyrics using the song's unique Genius ID
            song = genius.search_song(song_id=selected_hit['id'])
            
            if song and song.lyrics:
                clean_lyrics = clean_genius_artifacts(song.lyrics)
                preview = get_lyrics_preview(clean_lyrics)
                
                # Display the formatted preview
                print("\n" + "="*45)
                print(f"🎶 Title:  {song.title}")
                print(f"🎤 Artist: {song.artist}")
                print("-" * 45)
                print("📝 Lyric Preview:")
                print(preview)
                print("="*45 + "\n")
                
                # Ask to save
                save_choice = input("Save this song? (y = yes / n = no): ").strip().lower()
                
                if save_choice == 'y':
                    if not os.path.exists(TARGET_FOLDER):
                        os.makedirs(TARGET_FOLDER)
                        
                    filename = os.path.join(TARGET_FOLDER, f"{clean_filename(song.title)}.txt")
                    
                    # Save exactly how generator.py expects it
                    file_content = f"{song.title}\n{song.artist}\nlyrics\n{clean_lyrics}"
                    
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(file_content)
                    
                    print(f"✅ Saved perfectly to: {filename}")
                else:
                    print("⏭️ Skipped.")
            else:
                print("❌ Could not fetch lyrics for this song (it might be an instrumental).")
            
            # Pause so you can read the success/skip message before the list reprints
            input("\nPress Enter to return to the list...")

if __name__ == "__main__":
    run_interactive_engine()