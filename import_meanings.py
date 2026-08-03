import os
import json
import sys
import time
import requests
import urllib.parse

DIR_PATH = "raw_lyrics"
JSON_FILE = "completed_meanings.json"

meanings_data = None

def search_apple_music(title, artist):
    """Searches the iTunes API and returns the Track ID."""
    query = urllib.parse.quote(f"{title} {artist}")
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('resultCount', 0) > 0:
            track_id = data['results'][0]['trackId']
            return str(track_id)
        else:
            return "NONE" 
    except Exception as e:
        print(f"  -> Apple Music Search Error: {e}")
        return "NONE"

# Check if file exists, otherwise prompt for direct terminal input
if os.path.exists(JSON_FILE):
    print(f"📄 Found {JSON_FILE}, loading...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        meanings_data = json.load(f)
else:
    print("📋 Paste the AI JSON output directly into the terminal below.")
    print("👉 Once pasted, press Enter, then press Ctrl+Z and Enter (on Windows) to submit:\n")
    
    raw_input = sys.stdin.read()
    
    # Extract JSON array even if extra conversational text or markdown was pasted
    try:
        start_idx = raw_input.find('[')
        end_idx = raw_input.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = raw_input[start_idx:end_idx]
            meanings_data = json.loads(json_str)
        else:
            meanings_data = json.loads(raw_input)
    except Exception as e:
        print(f"\n❌ Invalid JSON received. Error details: {e}")
        exit()

print(f"\n📥 Processing {len(meanings_data)} songs...")

for item in meanings_data:
    filename = item.get("filename")
    meaning = item.get("meaning")
    
    if not filename or not meaning:
        continue
        
    filepath = os.path.join(DIR_PATH, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filename}")
        continue
        
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Check if meaning already exists to prevent double processing
    if len(lines) >= 3 and lines[2].strip().lower() == "meaning":
        print(f"⏭️ Skipping {filename} - already processed.")
        continue
        
    title = lines[0].strip()
    artist = lines[1].strip()

    # 1. Fetch Apple Music Data
    print(f"🎵 Fetching Apple Music ID for '{title}'...")
    track_id = search_apple_music(title, artist)
        
    # 2. Rebuild file with injected meaning and Apple data
    new_content = [
        f"{title}\n",
        f"{artist}\n",
        "meaning\n",
        f"{meaning}\n",
        "apple_data\n",
        f"{track_id}\n",
        "lyrics\n"
    ]
    
    # 3. Determine where the actual lyrics start in the original file
    lyrics_start_index = 2
    for i, line in enumerate(lines):
        if line.strip().lower() == "lyrics":
            lyrics_start_index = i + 1 
            break
            
    new_content.extend(lines[lyrics_start_index:])
    
    # 4. Save the file
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_content)
        
    print(f"✅ Updated {filename} (Track ID: {track_id})")
    
    # Slight pause to avoid hitting iTunes API rate limits too quickly
    time.sleep(1)

print("\n🎉 Batch update complete!")