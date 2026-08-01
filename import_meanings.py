import os
import json
import sys

DIR_PATH = "raw_lyrics"
JSON_FILE = "completed_meanings.json"

meanings_data = None

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

print(f"\n📥 Processing {len(meanings_data)} meanings...")

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
        
    # Check if meaning already exists
    if len(lines) >= 3 and lines[2].strip().lower() == "meaning":
        print(f"⏭️ Skipping {filename} - meaning already exists.")
        continue
        
    # Rebuild file with injected meaning
    new_content = [
        lines[0], # Title
        lines[1], # Artist
        "meaning\n",
        f"{meaning}\n"
    ]
    
    # Append the rest of the original content
    new_content.extend(lines[2:])
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_content)
        
    print(f"✅ Updated {filename}")

print("\n🎉 Batch update complete!")