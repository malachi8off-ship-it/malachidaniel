import os
import json
import subprocess

DIR_PATH = "raw_lyrics"
pending_songs = []

print("🔍 Scanning raw_lyrics for missing meanings...")

for filename in os.listdir(DIR_PATH):
    if not filename.endswith(".txt"):
        continue
        
    filepath = os.path.join(DIR_PATH, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Check if the file is long enough and if line 3 is already "meaning"
    if len(lines) >= 3 and lines[2].strip().lower() == "meaning":
        continue 
        
    # If it doesn't have a meaning, grab the title and artist
    title = lines[0].strip()
    artist = lines[1].strip()
    
    pending_songs.append({
        "filename": filename,
        "title": title,
        "artist": artist
    })

if not pending_songs:
    print("✅ No songs are missing meanings. You are all caught up!")
    exit()

# Define the exact prompt instructions for the AI
ai_prompt = """Please write a 2 to 3 sentence summary about the following Christian worship songs, including their core meaning and biblical context. 
IMPORTANT: If the song is sung in Hindi, Malayalam, Hinglish, or Manglish, you MUST explicitly mention that specific language/style in your summary. Keep it objective and informative.

Return the output STRICTLY in the following JSON array format. Do not include any markdown formatting, code blocks, or conversational text outside of the JSON array:

[
    {
        "filename": "...",
        "meaning": "..."
    }
]

Here is the list of songs to process:
"""

# Combine instructions and the JSON list
full_export_content = ai_prompt + json.dumps(pending_songs, indent=4)

# Copy directly to Windows clipboard
try:
    subprocess.run(
        ['clip.exe'], 
        input=full_export_content.strip().encode('utf-8'), 
        check=True
    )
    print(f"✅ Found {len(pending_songs)} songs missing meanings.")
    print("📋 The prompt and JSON list have been copied directly to your clipboard!")
    print("➡️  Just go to the AI chat and press Ctrl+V to paste.")
except Exception as e:
    print(f"❌ Failed to copy to clipboard: {e}")
    # Fallback to file just in case the clipboard command fails
    with open("pending_songs_prompt.txt", "w", encoding="utf-8") as f:
        f.write(full_export_content)
    print("📁 Saved to 'pending_songs_prompt.txt' as a fallback.")