import os
import time
import requests
import urllib.parse
from google import genai
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- CONFIGURATION ---
# Fetch the key securely from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-3.5-flash-lite'

DIR_PATH = "raw_lyrics"

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

def process_files():
    for filename in os.listdir(DIR_PATH):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(DIR_PATH, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Failsafe: Skip if file is empty or already processed
        if len(lines) < 3 or lines[2].strip().lower() == "meaning":
            print(f"⏭️ Skipping {filename} (Already processed or invalid)")
            continue
            
        title = lines[0].strip()
        artist = lines[1].strip()
        
        print(f"🔄 Processing: {title} by {artist}...")
        
        # 1. Fetch Apple Music Data
        track_id = search_apple_music(title, artist)
        print(f"  -> Apple Track ID: {track_id}")
        
        # 2. Fetch AI Meaning
        prompt = f"Write a 2 to 3 sentence summary about the Christian worship song '{title}' by '{artist}', including its core meaning and biblical context. Keep it objective, informative, and format it as a single paragraph."
        
        try:
            # NEW SYNTAX FOR GOOGLE GENAI SDK
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt
            )
            meaning = response.text.strip().replace('\n', ' ')
            print(f"  -> Generated Meaning Successfully.")
            
            # 3. Rebuild the file structure
            new_content = [
                f"{title}\n",
                f"{artist}\n",
                "meaning\n",
                f"{meaning}\n",
                "apple_data\n",
                f"{track_id}\n",
            ]
            
            # Find where the lyrics start in the original file
            lyrics_start_index = 0
            for i, line in enumerate(lines):
                if line.strip().lower() == "lyrics":
                    lyrics_start_index = i
                    break
                    
            # Append everything from "lyrics" downwards
            original_lyrics = lines[lyrics_start_index:]
            new_content.extend(original_lyrics)
            
            # 4. Overwrite the file
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(new_content)
                
            print(f"✅ Successfully updated {filename}\n")
            
            # Pause for 4 seconds to respect rate limits
            time.sleep(8) 
            
        except Exception as e:
            print(f"❌ Error processing AI for {filename}: {e}\n")

if __name__ == "__main__":
    print("Starting Bulk Contextualization Pipeline...\n")
    process_files()
    print("Pipeline Complete!")