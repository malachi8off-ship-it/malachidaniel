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
# 1. LYRICS GENERATOR LOGIC
# ==========================================
songs_data = []
for filename in os.listdir(lyrics_input):
    if filename.endswith('.txt'):
        with open(os.path.join(lyrics_input, filename), 'r', encoding='utf-8') as file:
            lines = file.readlines()
            title = lines[0].strip()
            author = lines[1].strip()
            lyrics = "<br>".join([line.strip() for line in lines[2:]])
            
            songs_data.append({'title': title, 'author': author, 'lyrics': lyrics, 'filename': filename.replace('.txt', '.html')})

songs_data.sort(key=lambda x: x['title'])
lyrics_cards = ""

# Generate individual song pages
for song in songs_data:
    html = master_template.replace('{{TITLE}}', song['title'])\
                          .replace('{{ARTIST}}', song['author'])\
                          .replace('{{CATEGORY}}', 'Lyrics')\
                          .replace('{{LYRICS_CONTENT}}', f'<p class="lyric-text">{song["lyrics"]}</p>')
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
base_url = "https://malachidaniel.pages.dev"
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

# Ensure the public folder exists just in case
os.makedirs('public', exist_ok=True)

# Copy your coming-soon.html and save it as index.html in the public folder
try:
    shutil.copy('coming-soon.html', 'public/index.html')
    print("Successfully created public/index.html from coming-soon.html")
except FileNotFoundError:
    print("Error: coming-soon.html not found in the root directory.")

# NEW: Copy the CSS file
try:
    shutil.copy('templates/style.css', 'public/style.css')
    print("Successfully copied style.css")
except FileNotFoundError:
    print("Error: templates/style.css not found.")
    
    # Copy your CSS to the public folder
shutil.copy('templates/style.css', 'public/style.css')

# Copy your new homepage and name it index.html for Cloudflare
shutil.copy('home.html', 'public/index.html')