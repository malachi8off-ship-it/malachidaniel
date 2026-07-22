import os
import re

def slugify(text):
    """Turns a track title into a clean filename (e.g., 'Amazing Grace!' -> 'amazing-grace')"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def main():
    target_dir = 'raw_karaoke'
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print("--- KARAOKE FILE GENERATOR ---")
    
    # 1. Get Track Details
    title = input("Enter Track Title: ").strip()
    if not title:
        print("Title cannot be empty!")
        return
        
    yt_link = input("Enter YouTube Link: ").strip()
    if not yt_link:
        print("YouTube link cannot be empty!")
        return

    # 2. Get Description
    print("\nPaste or type the track description below.")
    print("When you are completely finished, type 'DONE' on a new line and press Enter:")
    
    desc_lines = []
    while True:
        line = input()
        if line.strip() == "DONE":
            break
        desc_lines.append(line)

    # 3. Create the text file structure
    filename = f"{slugify(title)}.txt"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(f"{title}\n")
        file.write(f"{yt_link}\n")
        for line in desc_lines:
            file.write(f"{line}\n")

    print(f"\n Success! Saved as '{filepath}'")
    print("Now run 'python generator.py' to update your site!")

if __name__ == '__main__':
    main()