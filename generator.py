import os
import datetime
import shutil

# --- BULLETPROOF PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

lyrics_input = os.path.join(BASE_DIR, 'raw_lyrics')
lyrics_output = os.path.join(BASE_DIR, 'public', 'lyrics-archive')
karaoke_input = os.path.join(BASE_DIR, 'raw_karaoke')
karaoke_output = os.path.join(BASE_DIR, 'public', 'karaoke-tracks')
template_path = os.path.join(BASE_DIR, 'templates', 'master_template.html')
css_input = os.path.join(BASE_DIR, 'templates', 'style.css')
css_output = os.path.join(BASE_DIR, 'public', 'style.css')
request_input = os.path.join(BASE_DIR, 'templates', 'request.html')
request_output = os.path.join(BASE_DIR, 'public', 'request.html')

# Ensure all folders exist
for directory in [lyrics_output, karaoke_output, lyrics_input, karaoke_input]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# ==========================================
# 0. LOAD CUSTOM UI & COPY STATIC FILES
# ==========================================
if not os.path.exists(template_path):
    print(f"ERROR: Cannot find your template at {template_path}. Make sure it exists!")
    exit()

# Copy the modern style.css to the public folder
if os.path.exists(css_input):
    shutil.copy2(css_input, css_output)
else:
    print(f"WARNING: Cannot find {css_input}. Styling will be broken!")

# Copy the request.html to the public folder
if os.path.exists(request_input):
    shutil.copy2(request_input, request_output)
elif os.path.exists(os.path.join(BASE_DIR, 'request.html')):
    # Fallback just in case you saved it in the root folder instead of /templates
    shutil.copy2(os.path.join(BASE_DIR, 'request.html'), request_output)
else:
    print("WARNING: Cannot find request.html!")

with open(template_path, 'r', encoding='utf-8') as f:
    master_template = f.read()

# Fix routing paths for subfolders automatically
master_template = master_template.replace('href="style.css"', 'href="../style.css"')
master_template = master_template.replace('href="request.html"', 'href="../request.html"')
master_template = master_template.replace('href="/"', 'href="../index.html"')


# ==========================================
# 1. LYRICS GENERATOR LOGIC (UPDATED PARSER & LAYOUT)
# ==========================================
songs_data = []
for filename in os.listdir(lyrics_input):
    if filename.endswith('.txt'):
        with open(os.path.join(lyrics_input, filename), 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
            
            if len(lines) >= 2:
                title = lines[0]
                author = lines[1]
                
                meaning_text = ""
                apple_id = ""
                lyrics_text = ""
                
                # Check if the file has been processed with meaning & apple_data headers
                if "meaning" in lines and "apple_data" in lines and "lyrics" in lines:
                    idx_meaning = lines.index("meaning")
                    idx_apple = lines.index("apple_data")
                    idx_lyrics = lines.index("lyrics")
                    
                    meaning_lines = lines[idx_meaning + 1 : idx_apple]
                    meaning_text = " ".join([m for m in meaning_lines if m])
                    
                    apple_lines = lines[idx_apple + 1 : idx_lyrics]
                    apple_id = apple_lines[0] if apple_lines else ""
                    
                    lyrics_lines = lines[idx_lyrics + 1 :]
                    
                    # FILTER: Remove consecutive empty lines to fix massive spacing gaps
                    cleaned_lyrics = []
                    for line in lyrics_lines:
                        if line == "" and (len(cleaned_lyrics) == 0 or cleaned_lyrics[-1] == ""):
                            continue
                        cleaned_lyrics.append(line)
                    lyrics_text = "<br>".join(cleaned_lyrics)
                else:
                    # Fallback parsing for unprocessed files
                    lyrics_text = "<br>".join([l for l in lines[2:] if l])
                
                songs_data.append({
                    'title': title, 
                    'author': author, 
                    'meaning': meaning_text,
                    'apple_id': apple_id,
                    'lyrics': lyrics_text, 
                    'filename': filename.replace('.txt', '.html')
                })

songs_data.sort(key=lambda x: x['title'])
lyrics_cards = ""

# Generate individual song pages
for song in songs_data:
    full_song_content = ""
    
    # 1. Add Interactive Apple Music Player Widget (if ID exists)
    if song['apple_id']:
        full_song_content += f'''
<div style="margin-bottom: 2rem; width: 100%; display: flex; justify-content: center;">
    <iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="150" style="width:100%;max-width:660px;overflow:hidden;border-radius:12px;border: 1px solid var(--border-color); background: transparent;" sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation" src="https://embed.music.apple.com/us/album/-/1?i={song['apple_id']}"></iframe>
</div>
'''
    
    # 2. Add Lyrics Content (Moved above meaning)
    full_song_content += f'<div class="lyric-text" style="line-height: 1.7; font-size: 1.05rem; margin-bottom: 3rem; text-align: center;">{song["lyrics"]}</div>'

 # 3. Add AI Song Meaning Box (Moved to bottom)
    if song['meaning']:
        # Aggressively clean up hidden AI line breaks AND literal HTML <br> tags
        clean_meaning = " ".join([word for word in song['meaning'].split() if word])
        clean_meaning = clean_meaning.replace('<br>', '').replace('<br/>', '').strip()
        
        full_song_content += f'''
<div style="background-color: var(--card-bg); border: 1px solid var(--border-color); border-left: 4px solid var(--accent-color); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; display: block !important; height: auto !important; min-height: 0 !important;">
    <h3 style="margin: 0 0 1rem 0; color: var(--accent-color); font-size: 1.1rem;">
        💡 Song Meaning & Background
    </h3>
    <p style="margin: 0; line-height: 1.7; color: var(--text-color); font-size: 0.95rem;">
        {clean_meaning}
    </p>
</div>
'''

    html = master_template.replace('{{TITLE}}', song['title'])\
                           .replace('{{ARTIST}}', song['author'])\
                           .replace('{{CATEGORY}}', 'Lyrics')\
                           .replace('{{LYRICS_CONTENT}}', full_song_content)
                           
    with open(os.path.join(lyrics_output, song['filename']), 'w', encoding='utf-8') as f: 
        f.write(html)
        
    # Updated to use CSS variables for dark mode compatibility
    lyrics_cards += f'<a href="{song["filename"]}" style="text-decoration: none; color: inherit; display: block; margin-bottom: 15px;"><article style="padding: 1.5rem; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; transition: transform 0.2s;" class="interactive-card"><h3 style="color: var(--accent-color); margin-bottom: 0.5rem;">{song["title"]}</h3><p style="color: var(--muted-text); font-weight: 500;"><strong>By:</strong> {song["author"]}</p></article></a>'

# Generate the Lyrics Search (Index) Page
search_content = f"""
<div style="margin-bottom: 25px;">
    <input type="text" id="searchInput" placeholder="Search for a song..." style="width: 100%; padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); background-color: var(--bg-color); color: var(--text-color); font-family: var(--ui-font); font-size: 1rem;">
</div>
<div>{lyrics_cards}</div>
<script>
    document.getElementById('searchInput').addEventListener('keyup', function() {{
        let input = this.value.toLowerCase();
        let cards = document.getElementsByClassName('interactive-card');
        for (let i = 0; i < cards.length; i++) {{
            cards[i].parentElement.style.display = cards[i].innerText.toLowerCase().includes(input) ? "" : "none";
        }}
    }});
</script>
"""
index_html = master_template.replace('{{TITLE}}', 'Lyrics Archive')\
                            .replace('{{ARTIST}}', 'All Available Songs')\
                            .replace('{{CATEGORY}}', 'Archive')\
                            .replace('{{LYRICS_CONTENT}}', search_content)
with open(os.path.join(lyrics_output, 'index.html'), 'w', encoding='utf-8') as f: 
    f.write(index_html)


# ==========================================
# 2. KARAOKE YOUTUBE GENERATOR LOGIC
# ==========================================
karaoke_data = []
for filename in os.listdir(karaoke_input):
    if filename.endswith('.txt'):
        with open(os.path.join(karaoke_input, filename), 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines() if line.strip() != ""]
            if len(lines) >= 3:
                raw_link = lines[1]
                video_id = raw_link.split("v=")[1][:11] if "v=" in raw_link else (raw_link.split("youtu.be/")[1][:11] if "youtu.be/" in raw_link else raw_link)
                
                karaoke_data.append({'title': lines[0], 'video_id': video_id, 'desc': "<br>".join(lines[2:]), 'filename': filename.replace('.txt', '.html')})

karaoke_data.sort(key=lambda x: x['title'])
karaoke_cards = ""

# Generate individual karaoke pages
for track in karaoke_data:
    iframe_content = f"""
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 8px; background-color: #000; border: 1px solid var(--border-color);">
        <iframe src="https://www.youtube.com/embed/{track['video_id']}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen></iframe>
    </div>
    <p style="margin-top: 20px; font-size: 1.1rem;">{track['desc']}</p>
    """
    html = master_template.replace('{{TITLE}}', track['title'])\
                          .replace('{{ARTIST}}', 'Karaoke Track')\
                          .replace('{{CATEGORY}}', 'Karaoke')\
                          .replace('{{LYRICS_CONTENT}}', iframe_content)
    with open(os.path.join(karaoke_output, track['filename']), 'w', encoding='utf-8') as f: 
        f.write(html)
        
    # Updated to use CSS variables for dark mode compatibility
    karaoke_cards += f'<a href="{track["filename"]}" style="text-decoration: none; color: inherit; display: block; margin-bottom: 15px;"><article style="padding: 1.5rem; background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; transition: transform 0.2s;" class="interactive-card"><h3 style="color: var(--accent-color); margin-bottom: 0.5rem;">{track["title"]}</h3><p style="color: var(--muted-text); font-weight: 500;">▶ Play Track</p></article></a>'

# Generate the Karaoke Search (Index) Page
k_search_content = search_content.replace('Search for a song...', 'Search for a karaoke track...').replace(lyrics_cards, karaoke_cards)
k_index_html = master_template.replace('{{TITLE}}', 'Karaoke Tracks')\
                              .replace('{{ARTIST}}', 'All Available Karaoke')\
                              .replace('{{CATEGORY}}', 'Archive')\
                              .replace('{{LYRICS_CONTENT}}', k_search_content)
with open(os.path.join(karaoke_output, 'index.html'), 'w', encoding='utf-8') as f: 
    f.write(k_index_html)

print("Success! Hubs and static files fully generated.")

# ==========================================
# 3. AUTOMATED SEO SITEMAP GENERATOR
# ==========================================
base_url = "https://malachidaniel.com"
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
def add_url_to_sitemap(path):
    return f"  <url>\n    <loc>{base_url}/{path}</loc>\n    <lastmod>{current_date}</lastmod>\n  </url>\n"

for path in ["", "request.html", "lyrics-archive/index.html", "karaoke-tracks/index.html"]:
    sitemap_content += add_url_to_sitemap(path)
for song in songs_data:
    sitemap_content += add_url_to_sitemap(f"lyrics-archive/{song['filename']}")
for track in karaoke_data:
    sitemap_content += add_url_to_sitemap(f"karaoke-tracks/{track['filename']}")

sitemap_content += '</urlset>'
with open(os.path.join(BASE_DIR, 'public', 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print("SEO Sitemap successfully generated!")

# Ensure the public folder exists
os.makedirs('public', exist_ok=True)

# Copy asset files to public directory
if os.path.exists('templates/style.css'):
    shutil.copy('templates/style.css', 'public/style.css')

if os.path.exists('templates/hub.css'):
    shutil.copy('templates/hub.css', 'public/hub.css')

if os.path.exists('home.html'):
    shutil.copy('home.html', 'public/index.html')

if os.path.exists('logo.png'):
    shutil.copy('logo.png', 'public/logo.png')

if os.path.exists('coming-soon.html'):
    shutil.copy('coming-soon.html', 'public/coming-soon.html')

if os.path.exists('templates/request.html'):
    shutil.copy('templates/request.html', 'public/request.html')