import os
import datetime
import shutil
import re
import urllib.request
import json

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
presenter_input = os.path.join(BASE_DIR, 'templates', 'presenter.html')
artwork_cache_file = os.path.join(BASE_DIR, 'artwork_cache.json')

# Ensure all folders exist
for directory in [lyrics_output, karaoke_output, lyrics_input, karaoke_input]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Load existing artwork cache
if os.path.exists(artwork_cache_file):
    with open(artwork_cache_file, 'r', encoding='utf-8') as f:
        artwork_cache = json.load(f)
else:
    artwork_cache = {}

def get_itunes_artwork(apple_id):
    if not apple_id or apple_id.upper() == "NONE":
        return "../logo.png"
    if apple_id in artwork_cache:
        return artwork_cache[apple_id]
    
    try:
        url = f"https://itunes.apple.com/lookup?id={apple_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['resultCount'] > 0:
                art_url = data['results'][0]['artworkUrl100'].replace('100x100bb', '600x600bb')
                artwork_cache[apple_id] = art_url
                return art_url
    except Exception as e:
        print(f"Artwork fetch failed for ID {apple_id}: {e}")
    return "../logo.png"

# ==========================================
# 0. LOAD CUSTOM UI & COPY STATIC FILES
# ==========================================
if not os.path.exists(template_path):
    print(f"ERROR: Cannot find your template at {template_path}. Make sure it exists!")
    exit()

if os.path.exists(css_input): shutil.copy2(css_input, css_output)
if os.path.exists(request_input): shutil.copy2(request_input, request_output)
elif os.path.exists(os.path.join(BASE_DIR, 'request.html')): shutil.copy2(os.path.join(BASE_DIR, 'request.html'), request_output)
if os.path.exists(presenter_input): shutil.copy2(presenter_input, os.path.join(BASE_DIR, 'public', 'presenter.html'))

with open(template_path, 'r', encoding='utf-8') as f:
    master_template = f.read()

master_template = master_template.replace('href="style.css"', 'href="../style.css"')
master_template = master_template.replace('href="request.html"', 'href="../request.html"')
master_template = master_template.replace('href="/"', 'href="../index.html"')

def detect_language(text_to_check, lyrics_text=""):
    text_to_check = text_to_check.lower()
    if "malayalam" in text_to_check or "manglish" in text_to_check or any('\u0D00' <= c <= '\u0D7F' for c in lyrics_text):
        return "malayalam"
    elif "hindi" in text_to_check or "hinglish" in text_to_check or any('\u0900' <= c <= '\u097F' for c in lyrics_text):
        return "hindi"
    return "english"

# ==========================================
# 1. LYRICS GENERATOR LOGIC
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
                
                if "meaning" in lines and "apple_data" in lines:
                    idx_meaning = lines.index("meaning")
                    idx_apple = lines.index("apple_data")
                    meaning_lines = lines[idx_meaning + 1 : idx_apple]
                    meaning_text = " ".join([m for m in meaning_lines if m])
                    
                    if "lyrics" in lines:
                        idx_lyrics = lines.index("lyrics")
                        apple_lines = lines[idx_apple + 1 : idx_lyrics]
                        apple_id = apple_lines[0] if apple_lines else ""
                        lyrics_lines = lines[idx_lyrics + 1 :]
                    else:
                        apple_id = lines[idx_apple + 1] if len(lines) > idx_apple + 1 else ""
                        raw_lyrics = lines[idx_apple + 2 :]
                        if len(raw_lyrics) >= 2 and raw_lyrics[0] == title and raw_lyrics[1] == author:
                            lyrics_lines = raw_lyrics[2:]
                        else:
                            lyrics_lines = raw_lyrics
                    
                    apple_id = apple_id if apple_id.upper() != "NONE" else ""
                    cleaned_lyrics = []
                    for line in lyrics_lines:
                        if line == "" and (len(cleaned_lyrics) == 0 or cleaned_lyrics[-1] == ""): continue
                        cleaned_lyrics.append(line)
                    lyrics_text = "<br>".join(cleaned_lyrics)
                else:
                    lyrics_text = "<br>".join([l for l in lines[2:] if l])
                
                lang_attr = detect_language(title + " " + meaning_text, lyrics_text)
                
                songs_data.append({
                    'title': title, 
                    'author': author, 
                    'meaning': meaning_text,
                    'apple_id': apple_id,
                    'lyrics': lyrics_text, 
                    'filename': filename.replace('.txt', '.html'),
                    'language': lang_attr
                })

songs_data.sort(key=lambda x: x['title'])
lyrics_cards = ""
api_payload = []

for i, song in enumerate(songs_data):
    full_song_content = ""
    art_url = get_itunes_artwork(song['apple_id'])
    
    # 1. ADD TO JSON API PAYLOAD
    api_payload.append({
        'id': song['filename'],
        'title': song['title'],
        'author': song['author'],
        'lyrics': song['lyrics']
    })
    
    if song['apple_id']:
        full_song_content += f'''
<div class="player-container">
    <iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="150" class="apple-iframe" sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation" src="https://embed.music.apple.com/us/album/-/1?i={song['apple_id']}"></iframe>
</div>
'''
    # 2. INJECT PRESENTER VIEW BUTTON
    full_song_content += f'''
<div style="margin-top: 25px; margin-bottom: 30px; text-align: center;">
    <a href="../presenter.html?song={song['filename']}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: rgba(52, 152, 219, 0.1); border: 1px solid #3498db; color: #3498db; padding: 12px 25px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 0.95rem; transition: all 0.2s;">
        📺 Launch Presenter View
    </a>
</div>
'''
    full_song_content += f'<div class="lyric-text">{song["lyrics"]}</div>'

    if song['meaning']:
        clean_meaning = " ".join([word for word in song['meaning'].split() if word]).replace('<br>', '').replace('<br/>', '').strip()
        full_song_content += f'''
<div class="meaning-container">
    <div class="meaning-card">
        <h3>&#128161; Song Meaning & Background</h3>
        <p>{clean_meaning}</p>
    </div>
</div>
'''
    html = master_template.replace('{{TITLE}}', song['title'])\
                           .replace('{{ARTIST}}', song['author'])\
                           .replace('{{CATEGORY}}', 'Lyrics')\
                           .replace('{{LYRICS_CONTENT}}', full_song_content)\
                           .replace('{{BACK_URL}}', 'index.html')\
                           .replace('{{BACK_TEXT}}', 'Back to Lyrics Hub')
                           
    with open(os.path.join(lyrics_output, song['filename']), 'w', encoding='utf-8') as f: 
        f.write(html)
        
    track_num = str(i + 1).zfill(2)
    display_lang = song['language'].capitalize() if song['language'] != 'english' else 'Worship'
    song_identifier = song['apple_id'] if song['apple_id'] else song['title']
    
    full_txt_path = os.path.join(lyrics_input, song['filename'].replace('.html', '.txt'))
    creation_time = os.path.getctime(full_txt_path) if os.path.exists(full_txt_path) else 0
    clean_title = re.sub(r'^[\d\s\-]+', '', song["title"]).lower()
    
    lyrics_cards += f'''
    <a href="{song["filename"]}" class="song-card interactive-card" data-index="{i}" data-time="{creation_time}" data-sort-name="{clean_title}" data-language="{song["language"]}" data-title="{song["title"].lower()} {song["author"].lower()}">
        <div class="card-top">
            <div class="thumbnail-wrapper">
                <img src="{art_url}" class="album-thumb" alt="Cover" onerror="this.src='../logo.png'">
            </div>
            <div class="card-meta">
                <h3 class="card-title">{song["author"]}</h3>
                <p class="card-subtitle">{song["title"]}</p>
                <div class="tags">
                    <span class="tag tag-num">{track_num}</span>
                    <span class="tag tag-genre">{display_lang}</span>
                    <span class="tag tag-vibe">Uplifting</span>
                </div>
            </div>
            <div class="heart-icon" data-id="{song_identifier}">&#9825;</div>
        </div>
        
        <p class="full-title">{track_num} - {song["author"]} - {song["title"]}</p>
        <p class="by-line">By: {song["author"]}</p>
        
        <div class="btn-play-lyrics">&#9654; Play Lyrics</div>
        
        <div class="card-footer">
            <span class="play-count">&#8857; Plays</span>
            <span class="rating">&#9733;&#9733;&#9733;&#9733;&#9733; 50</span>
        </div>
    </a>
    '''

# 3. WRITE THE JSON API FILE
with open(os.path.join(BASE_DIR, 'public', 'lyrics_api.json'), 'w', encoding='utf-8') as f:
    json.dump(api_payload, f)

search_content = f'''
<div class="glass-search-container">
    <div class="search-input-wrapper">
        <span class="search-icon">&#128269;</span>
        <input type="text" id="searchInput" placeholder="Search by Artist, Song Title, or Lyrics...">
        <span class="clear-icon" id="clearSearch">&#10005;</span>
    </div>
    
    <div class="filter-controls">
        <div class="filter-group">
            <label>Language &#127482;&#127480; &#127470;&#127475; &#127988; &#127474;&#127485;</label>
            <div class="select-wrapper">
                <span class="globe-icon">&#127757;</span>
                <select id="langFilter">
                    <option value="all">All Languages</option>
                    <option value="english">English</option>
                    <option value="hindi">Hindi</option>
                    <option value="malayalam">Malayalam</option>
                </select>
            </div>
        </div>
        
        <div class="filter-group">
            <label>Sort by</label>
            <div class="sort-tabs">
                <span class="sort-tab" data-sort="favorites">Favorites</span>
                <span class="sort-tab active" data-sort="alphabetical">Alphabetical</span>
                <span class="sort-tab" data-sort="recent">Recently Added</span>
            </div>
        </div>
    </div>
</div>

<div class="lyrics-grid" id="lyricsGrid">
    {lyrics_cards}
</div>

<script>
    let favorites = JSON.parse(localStorage.getItem('lyric_favorites')) || [];

    document.querySelectorAll('.heart-icon').forEach(icon => {{
        let songId = icon.getAttribute('data-id');
        if (favorites.includes(songId)) {{
            icon.classList.add('active');
            icon.innerHTML = '&#9829;'; 
        }}
        
        icon.addEventListener('click', function(e) {{
            e.preventDefault(); 
            e.stopPropagation();
            
            let index = favorites.indexOf(songId);
            if (index === -1) {{
                favorites.push(songId);
                this.classList.add('active');
                this.innerHTML = '&#9829;';
            }} else {{
                favorites.splice(index, 1);
                this.classList.remove('active');
                this.innerHTML = '&#9825;'; 
            }}
            localStorage.setItem('lyric_favorites', JSON.stringify(favorites));
            
            if (currentSort === 'favorites') filterItems();
        }});
    }});

    let currentSort = 'alphabetical';
    
    document.querySelectorAll('.sort-tab').forEach(tab => {{
        tab.addEventListener('click', function() {{
            document.querySelectorAll('.sort-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentSort = this.getAttribute('data-sort');
            filterItems();
        }});
    }});

    function filterItems() {{
        let searchText = document.getElementById('searchInput').value.toLowerCase();
        let selectedLang = document.getElementById('langFilter').value;
        let cards = Array.from(document.getElementsByClassName('interactive-card'));
        let grid = document.getElementById('lyricsGrid');
        
        cards.forEach(card => {{
            let searchableText = card.getAttribute('data-title');
            let cardLang = card.getAttribute('data-language');
            
            let heartIcon = card.querySelector('.heart-icon');
            let songId = heartIcon ? heartIcon.getAttribute('data-id') : null;
            
            let matchesSearch = searchableText.includes(searchText);
            let matchesLang = (selectedLang === 'all' || cardLang === selectedLang);
            let matchesFav = (currentSort !== 'favorites' || (songId && favorites.includes(songId)));
            
            card.style.display = (matchesSearch && matchesLang && matchesFav) ? "flex" : "none";
        }});
        
        if (currentSort === 'alphabetical') {{
            cards.sort((a, b) => a.getAttribute('data-sort-name').localeCompare(b.getAttribute('data-sort-name')));
        }} else if (currentSort === 'recent') {{
            cards.sort((a, b) => parseFloat(b.getAttribute('data-time')) - parseFloat(a.getAttribute('data-time')));
        }} else {{
            cards.sort((a, b) => parseInt(a.getAttribute('data-index')) - parseInt(b.getAttribute('data-index')));
        }}
        
        cards.forEach(card => grid.appendChild(card));
    }}
    
    filterItems();

    document.getElementById('searchInput').addEventListener('input', filterItems);
    document.getElementById('langFilter').addEventListener('change', filterItems);
    document.getElementById('clearSearch').addEventListener('click', () => {{
        document.getElementById('searchInput').value = '';
        filterItems();
    }});
</script>
'''

index_html = master_template.replace('{{TITLE}}', 'Lyrics Archive')\
                            .replace('{{ARTIST}}', 'All Available Songs')\
                            .replace('{{CATEGORY}}', 'Archive')\
                            .replace('{{LYRICS_CONTENT}}', search_content)\
                            .replace('{{BACK_URL}}', '../index.html')\
                            .replace('{{BACK_TEXT}}', 'Back to Main Hub')
                            
with open(os.path.join(lyrics_output, 'index.html'), 'w', encoding='utf-8') as f: 
    f.write(index_html)

with open(artwork_cache_file, 'w', encoding='utf-8') as f:
    json.dump(artwork_cache, f)

# ==========================================
# 2. KARAOKE YOUTUBE GENERATOR LOGIC
# ==========================================
karaoke_data = []
for filename in os.listdir(karaoke_input):
    if filename.endswith('.txt'):
        with open(os.path.join(karaoke_input, filename), 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines() if line.strip() != ""]
            if len(lines) >= 3:
                title = lines[0]
                raw_link = lines[1]
                desc = "<br>".join(lines[2:])
                video_id = raw_link.split("v=")[1][:11] if "v=" in raw_link else (raw_link.split("youtu.be/")[1][:11] if "youtu.be/" in raw_link else raw_link)
                lang_attr = detect_language(title + " " + desc)
                karaoke_data.append({'title': title, 'video_id': video_id, 'desc': desc, 'filename': filename.replace('.txt', '.html'), 'language': lang_attr})

karaoke_data.sort(key=lambda x: x['title'])
karaoke_cards = ""

for i, track in enumerate(karaoke_data):
    iframe_content = f'''
    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 8px; background-color: #000; border: 1px solid var(--border-color);">
        <iframe src="https://www.youtube.com/embed/{track['video_id']}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen></iframe>
    </div>
    <p style="margin-top: 20px; font-size: 1.1rem;">{track['desc']}</p>
    '''
    html = master_template.replace('{{TITLE}}', track['title'])\
                          .replace('{{ARTIST}}', 'Karaoke Track')\
                          .replace('{{CATEGORY}}', 'Karaoke')\
                          .replace('{{LYRICS_CONTENT}}', iframe_content)\
                          .replace('{{BACK_URL}}', 'index.html')\
                          .replace('{{BACK_TEXT}}', 'Back to Karaoke Hub')
                          
    with open(os.path.join(karaoke_output, track['filename']), 'w', encoding='utf-8') as f: 
        f.write(html)
        
    track_num = str(i + 1).zfill(2)
    full_txt_path = os.path.join(karaoke_input, track['filename'].replace('.html', '.txt'))
    creation_time = os.path.getctime(full_txt_path) if os.path.exists(full_txt_path) else 0
    clean_title = re.sub(r'^[\d\s\-]+', '', track["title"]).lower()
    
    karaoke_cards += f'''
    <a href="{track["filename"]}" class="song-card interactive-card" data-index="{i}" data-time="{creation_time}" data-sort-name="{clean_title}" data-language="{track["language"]}" data-title="{track["title"].lower()}">
        <div class="card-top">
            <div class="thumbnail-wrapper">
                <img src="https://img.youtube.com/vi/{track['video_id']}/hqdefault.jpg" class="album-thumb" alt="Thumbnail">
            </div>
            <div class="card-meta">
                <h3 class="card-title">Karaoke</h3>
                <p class="card-subtitle">{track["title"]}</p>
                <div class="tags">
                    <span class="tag tag-num">{track_num}</span>
                    <span class="tag tag-genre">Instrumental</span>
                </div>
            </div>
            <div class="heart-icon" style="display:none;"></div>
        </div>
        
        <p class="full-title">{track_num} - {track["title"]}</p>
        <p class="by-line">Instrumental Track</p>
        
        <div class="btn-play-lyrics">&#9654; Play Video</div>
        
        <div class="card-footer">
            <span class="play-count">&#8857; Plays</span>
            <span class="rating">&#9733;&#9733;&#9733;&#9733;&#9733; 50</span>
        </div>
    </a>
    '''

k_search_content = search_content.replace('Search by Artist, Song Title, or Lyrics...', 'Search for a karaoke track...').replace(lyrics_cards, karaoke_cards)
k_index_html = master_template.replace('{{TITLE}}', 'Karaoke Tracks')\
                              .replace('{{ARTIST}}', 'All Available Karaoke')\
                              .replace('{{CATEGORY}}', 'Archive')\
                              .replace('{{LYRICS_CONTENT}}', k_search_content)\
                              .replace('{{BACK_URL}}', '../index.html')\
                              .replace('{{BACK_TEXT}}', 'Back to Main Hub')
                              
with open(os.path.join(karaoke_output, 'index.html'), 'w', encoding='utf-8') as f: 
    f.write(k_index_html)

# ==========================================
# 3. GENERATE ROOT HUB & COMING SOON PAGES
# ==========================================
with open(template_path, 'r', encoding='utf-8') as f:
    root_template = f.read()

home_content = '''
<div class="glass-search-container" style="text-align: center; padding: 40px 20px;">
    <h2 style="margin-bottom: 30px; font-size: 1.8rem;">Explore the Channel</h2>
    
    <div class="lyrics-grid">
        <a href="lyrics-archive/index.html" class="song-card interactive-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-decoration: none; text-align: center; height: 100%;">
            <h3 class="card-title" style="font-size: 1.5rem; margin-bottom: 15px;">📖 Lyrics Archive</h3>
            <p class="card-subtitle" style="font-size: 1rem; white-space: normal; opacity: 0.9;">Search rare hymns and official songs.</p>
        </a>
        
        <a href="karaoke-tracks/index.html" class="song-card interactive-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-decoration: none; text-align: center; height: 100%;">
            <h3 class="card-title" style="font-size: 1.5rem; margin-bottom: 15px;">🎤 Karaoke Tracks</h3>
            <p class="card-subtitle" style="font-size: 1rem; white-space: normal; opacity: 0.9;">High-quality instrumentals for worship.</p>
        </a>
        
        <a href="coming-soon.html" class="song-card interactive-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-decoration: none; text-align: center; height: 100%;">
            <h3 class="card-title" style="font-size: 1.5rem; margin-bottom: 15px;">✨ Testimonies</h3>
            <p class="card-subtitle" style="font-size: 1rem; white-space: normal; opacity: 0.9;">Powerful stories and biblical reflections.</p>
        </a>
        
        <a href="coming-soon.html" class="song-card interactive-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; text-decoration: none; text-align: center; height: 100%;">
            <h3 class="card-title" style="font-size: 1.5rem; margin-bottom: 15px;">🎧 Remixes & Mashups</h3>
            <p class="card-subtitle" style="font-size: 1rem; white-space: normal; opacity: 0.9;">Listen to the latest channel releases.</p>
        </a>
    </div>
</div>
'''

home_html = root_template.replace('{{TITLE}}', 'Malachi Daniel Hub')\
                         .replace('{{ARTIST}}', 'Karaokes, Covers, Mashups & Rare Christian Lyrics')\
                         .replace('{{CATEGORY}}', 'Hub')\
                         .replace('{{LYRICS_CONTENT}}', home_content)\
                         .replace('{{BACK_URL}}', '#')\
                         .replace('{{BACK_TEXT}}', 'Welcome to the Hub')
                         
with open(os.path.join(BASE_DIR, 'public', 'index.html'), 'w', encoding='utf-8') as f:
    f.write(home_html)

coming_soon_content = '''
<div class="glass-search-container" style="text-align: center; padding: 60px 20px; margin-top: 20px;">
    <h2 style="margin-bottom: 20px; font-size: 2rem;">Coming Soon</h2>
    <p style="font-size: 1.2rem; line-height: 1.6; opacity: 0.8;">
        This section is currently being mixed and mastered.<br>
        Check back soon for new content.
    </p>
</div>
'''

cs_html = root_template.replace('{{TITLE}}', 'Work In Progress 🚧')\
                       .replace('{{ARTIST}}', 'We\'re Tuning Things Up!')\
                       .replace('{{CATEGORY}}', 'Coming Soon')\
                       .replace('{{LYRICS_CONTENT}}', coming_soon_content)\
                       .replace('{{BACK_URL}}', 'index.html')\
                       .replace('{{BACK_TEXT}}', 'Back to Main Hub')
                       
with open(os.path.join(BASE_DIR, 'public', 'coming-soon.html'), 'w', encoding='utf-8') as f:
    f.write(cs_html)

print("Success! Hubs, Root pages, and static files fully generated.")

# ==========================================
# 4. AUTOMATED SEO SITEMAP GENERATOR
# ==========================================
base_url = "https://malachidaniel.com"
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
def add_url_to_sitemap(path):
    return f"  <url>\n    <loc>{base_url}/{path}</loc>\n    <lastmod>{current_date}</lastmod>\n  </url>\n"

for path in ["", "request.html", "lyrics-archive/index.html", "karaoke-tracks/index.html", "coming-soon.html", "presenter.html"]:
    sitemap_content += add_url_to_sitemap(path)
for song in songs_data:
    sitemap_content += add_url_to_sitemap(f"lyrics-archive/{song['filename']}")
for track in karaoke_data:
    sitemap_content += add_url_to_sitemap(f"karaoke-tracks/{track['filename']}")

sitemap_content += '</urlset>'
with open(os.path.join(BASE_DIR, 'public', 'sitemap.xml'), 'w', encoding='utf-8') as f:
    f.write(sitemap_content)

print("SEO Sitemap successfully generated!")

os.makedirs('public', exist_ok=True)

# Copying over static assets
if os.path.exists('templates/style.css'): shutil.copy('templates/style.css', 'public/style.css')
if os.path.exists('templates/lighter-bg.jpg'): shutil.copy('templates/lighter-bg.jpg', 'public/lighter-bg.jpg')
if os.path.exists('templates/dark-bg.jpg'): shutil.copy('templates/dark-bg.jpg', 'public/dark-bg.jpg')
if os.path.exists('logo.png'): shutil.copy('logo.png', 'public/logo.png')
if os.path.exists('templates/request.html'): shutil.copy('templates/request.html', 'public/request.html')

if os.path.exists('favicon.ico'): shutil.copy('favicon.ico', 'public/favicon.ico')
if os.path.exists('apple-touch-icon.png'): shutil.copy('apple-touch-icon.png', 'public/apple-touch-icon.png')
if os.path.exists('favicon-32x32.png'): shutil.copy('favicon-32x32.png', 'public/favicon-32x32.png')
if os.path.exists('favicon-16x16.png'): shutil.copy('favicon-16x16.png', 'public/favicon-16x16.png')