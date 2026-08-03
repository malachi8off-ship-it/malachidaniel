import os
import requests
import urllib.parse
import time

DIR_PATH = "raw_lyrics"

def search_apple_music(title, artist):
    query = urllib.parse.quote(f"{title} {artist}")
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('resultCount', 0) > 0:
            return str(data['results'][0]['trackId'])
    except Exception as e:
        print(f"  -> Apple Music Search Error: {e}")
    return "NONE"

print("========================================")
print("     RETRO APPLE MUSIC ID FETCHER       ")
print("========================================")
print("🔍 Scanning raw_lyrics for missing Apple Music IDs...")

if not os.path.exists(DIR_PATH):
    print(f"❌ Directory '{DIR_PATH}' not found. Please run this in the project root.")
    exit()

updated_count = 0

for filename in os.listdir(DIR_PATH):
    if not filename.endswith(".txt"):
        continue
        
    filepath = os.path.join(DIR_PATH, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    if len(lines) < 3:
        continue
        
    # Check if apple_data already exists
    has_apple = any(line.strip().lower() == "apple_data" for line in lines)
    if has_apple:
        continue
        
    title = lines[0].strip()
    artist = lines[1].strip()
    
    print(f"🎵 Fetching Apple Music ID for '{title}' by '{artist}'...")
    track_id = search_apple_music(title, artist)
    
    # Locate insertion point
    lyrics_idx = -1
    meaning_idx = -1
    
    for i, line in enumerate(lines):
        val = line.strip().lower()
        if val == "lyrics":
            lyrics_idx = i
        elif val == "meaning":
            meaning_idx = i
            
    new_content = []
    
    if lyrics_idx != -1:
        # We found the lyrics tag, insert just before it
        new_content = lines[:lyrics_idx]
        new_content.extend(["apple_data\n", f"{track_id}\n"])
        new_content.extend(lines[lyrics_idx:])
    else:
        # No lyrics tag found
        if meaning_idx != -1:
            # Insert after meaning block (which is meaning tag + 1 line of text)
            insert_pos = meaning_idx + 2
        else:
            # No meaning either, insert after artist
            insert_pos = 2
            
        new_content = lines[:insert_pos]
        new_content.extend(["apple_data\n", f"{track_id}\n", "lyrics\n"])
        new_content.extend(lines[insert_pos:])
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_content)
        
    print(f"  ✅ Updated {filename} (Track ID: {track_id})")
    updated_count += 1
    time.sleep(1) # Be nice to Apple API

if updated_count == 0:
    print("\n✅ All files already have Apple Music data. You're all caught up!")
else:
    print(f"\n🎉 Successfully updated {updated_count} files with Apple Music IDs!")