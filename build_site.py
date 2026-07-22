import os

TEMPLATE_DIR = "templates"
LYRICS_DIR = "raw_lyrics"
OUTPUT_DIR = "public"

def setup_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(TEMPLATE_DIR, "style.css"), "r", encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(OUTPUT_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(css)
        
    with open(os.path.join(TEMPLATE_DIR, "request.html"), "r", encoding="utf-8") as f:
        req = f.read()
    with open(os.path.join(OUTPUT_DIR, "request.html"), "w", encoding="utf-8") as f:
        f.write(req)

def parse_lyric_file(file_path):
    """Robustly reads text file lines, extracts title/artist, and trims headers."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    clean_lines = [line.strip() for line in lines if line.strip()]
    
    title = ""
    artist = ""
    category = "Christian"
    lyrics_start_index = 0
    
    if len(clean_lines) >= 3:
        title = clean_lines[0].strip()
        artist = clean_lines[1].strip()
        
        for i, line in enumerate(clean_lines[:4]):
            if line.lower() == "lyrics":
                lyrics_start_index = i + 1
                break
        
        if lyrics_start_index == 0:
            lyrics_start_index = 2
            
        lyrics_content = "\n".join(clean_lines[lyrics_start_index:])
    else:
        lyrics_content = "\n".join(clean_lines)

    return title, artist, category, lyrics_content

def generate_site():
    setup_directories()
    
    template_path = os.path.join(TEMPLATE_DIR, "master_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html_blueprint = f.read()
        
    song_links = []
        
    for filename in os.listdir(LYRICS_DIR):
        if filename.endswith(".txt"):
            file_path = os.path.join(LYRICS_DIR, filename)
            
            title, artist, category, lyrics = parse_lyric_file(file_path)
            clean_fallback_title = filename.replace(".txt", "").replace("_", " ").replace("-", " ").title()
            
            if not title:
                title = clean_fallback_title
            if not artist:
                artist = "Unknown Artist"
                
            page_content = html_blueprint
            page_content = page_content.replace("{{TITLE}}", title)
            page_content = page_content.replace("{{ARTIST}}", artist)
            page_content = page_content.replace("{{CATEGORY}}", category)
            page_content = page_content.replace("{{LYRICS_CONTENT}}", lyrics)
            
            clean_url_name = filename.replace(".txt", ".html").replace("_", "-").replace(" ", "-").lower()
            output_path = os.path.join(OUTPUT_DIR, clean_url_name)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(page_content)
                
            print(f"Generated: {clean_url_name}")
            
            song_links.append(f'<li style="margin-bottom: 12px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px; transition: 0.3s;"><a href="{clean_url_name}" style="color: #4da6ff; text-decoration: none; font-weight: bold; font-size: 1.1em; display: block; font-family: var(--ui-font);">{title} <span style="color: #aaa; font-weight: normal; font-size: 0.9em; float: right;">{artist}</span></a></li>')

    if song_links:
        # FIX: Flattened the HTML strings onto a single line to prevent layout breaks
        search_html = '<div style="margin-bottom: 20px;"><input type="text" id="searchInput" placeholder="Search for a song or artist..." style="width: 100%; padding: 15px; border-radius: 8px; border: 1px solid #444; background: rgba(0,0,0,0.2); color: #fff; font-size: 16px; outline: none; font-family: var(--ui-font); box-sizing: border-box;"></div>'
        
        list_html = f"<ul id='songList' style='list-style: none; padding: 0; margin: 0;'>{''.join(song_links)}</ul>"
        
        js_script = "<script>document.getElementById('searchInput').addEventListener('keyup', function() { let filter = this.value.toLowerCase(); let lis = document.getElementById('songList').getElementsByTagName('li'); for (let i = 0; i < lis.length; i++) { let text = lis[i].textContent || lis[i].innerText; if (text.toLowerCase().indexOf(filter) > -1) { lis[i].style.display = ''; } else { lis[i].style.display = 'none'; } } });</script>"
        
        homepage_content = search_html + list_html + js_script
        
        index_content = html_blueprint
        index_content = index_content.replace("{{TITLE}}", "Song Library")
        index_content = index_content.replace("{{ARTIST}}", "Find your favorite lyrics")
        index_content = index_content.replace("{{CATEGORY}}", "Directory")
        index_content = index_content.replace("{{LYRICS_CONTENT}}", homepage_content)
        
        with open(os.path.join(OUTPUT_DIR, "lyrics.html"), "w", encoding="utf-8") as f:
            f.write(index_content)
        print("Generated: lyrics.html (Homepage with Search functionality!)")

if __name__ == "__main__":
    generate_site()