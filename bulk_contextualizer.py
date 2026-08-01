import os
import time
import requests
import urllib.parse
import random
from google import genai
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

DIR_PATH = "raw_lyrics"

# Initialize API Clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
) if OPENROUTER_API_KEY else None

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

def generate_with_gemini(prompt):
    if not gemini_client:
        raise ValueError("Gemini API Key missing")
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.strip().replace('\n', ' ')

def generate_with_groq(prompt):
    if not groq_client:
        raise ValueError("Groq API Key missing")
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return completion.choices[0].message.content.strip().replace('\n', ' ')

def generate_with_openrouter(prompt):
    if not openrouter_client:
        raise ValueError("OpenRouter API Key missing")
    completion = openrouter_client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return completion.choices[0].message.content.strip().replace('\n', ' ')

# List of available engines
available_engines = [
    ("Gemini", generate_with_gemini),
    ("Groq", generate_with_groq),
    ("OpenRouter", generate_with_openrouter)
]

def fetch_ai_meaning(prompt, filename):
    """Tries engines randomly until one succeeds."""
    random.shuffle(available_engines)
    
    for engine_name, generate_func in available_engines:
        try:
            print(f"  -> Attempting generation with {engine_name}...")
            meaning = generate_func(prompt)
            print(f"  -> Generated Meaning Successfully via {engine_name}.")
            return meaning
        except Exception as e:
            print(f"  -> ⚠️ {engine_name} failed: {e}. Retrying with next engine...")
            
    print(f"  -> ❌ All AI engines failed for {filename}.")
    return None

def process_files():
    for filename in os.listdir(DIR_PATH):
        if not filename.endswith(".txt"):
            continue
            
        filepath = os.path.join(DIR_PATH, filename)
        
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Failsafe
        if len(lines) < 3 or lines[2].strip().lower() == "meaning":
            continue
            
        title = lines[0].strip()
        artist = lines[1].strip()
        
        print(f"🔄 Processing: {title} by {artist}...")
        
        # 1. Fetch Apple Music Data
        track_id = search_apple_music(title, artist)
        print(f"  -> Apple Track ID: {track_id}")
        
        # 2. Fetch AI Meaning
        prompt = f"Write a 2 to 3 sentence summary about the Christian worship song '{title}' by '{artist}', including its core meaning and biblical context. Keep it objective, informative, and format it as a single paragraph."
        
        meaning = fetch_ai_meaning(prompt, filename)
        
        if not meaning:
            continue # Skip to next file if all engines fail
            
        # 3. Rebuild the file structure
        new_content = [
            f"{title}\n",
            f"{artist}\n",
            "meaning\n",
            f"{meaning}\n",
            "apple_data\n",
            f"{track_id}\n",
        ]
        
        lyrics_start_index = 0
        for i, line in enumerate(lines):
            if line.strip().lower() == "lyrics":
                lyrics_start_index = i
                break
                
        new_content.extend(lines[lyrics_start_index:])
        
        # 4. Overwrite the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_content)
            
        print(f"✅ Successfully updated {filename}\n")
        
        time.sleep(2) 

if __name__ == "__main__":
    print("Starting Bulk Contextualization Pipeline with API Pooling...\n")
    process_files()
    print("Pipeline Complete!")