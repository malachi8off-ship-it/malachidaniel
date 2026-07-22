import os
import re

def slugify(text):
    """Turns a song title into a clean filename (e.g., 'Amazing Grace!' -> 'amazing-grace')"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def main():
    target_dir = 'raw_lyrics'
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print("--- LYRICS FILE GENERATOR ---")
    
    # 1. Get Song Details
    title = input("Enter Song Title: ").strip()
    if not title:
        print("Title cannot be empty!")
        return
        
    author = input("Enter Artist/Author: ").strip()
    if not author:
        author = "Unknown"  # Fallback if you leave it blank

    # 2. Get Full Lyrics
    print("\nPaste or type the lyrics below.")
    print("When you are completely finished, type 'DONE' on a new line and press Enter:")
    
    lyrics_lines = []
    while True:
        line = input()
        if line.strip() == "DONE":
            break
        lyrics_lines.append(line)

    # 3. Create the text file structure
    filename = f"{slugify(title)}.txt"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(f"{title}\n")
        file.write(f"{author}\n")
        for line in lyrics_lines:
            file.write(f"{line}\n")

    print(f"\n Success! Saved as '{filepath}'")
    print("Now run 'python generator.py' to update your site!")

if __name__ == '__main__':
    main()