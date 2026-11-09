import os
import datetime
import shutil
import re
import urllib.request
import urllib.parse
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

chords_input = os.path.join(BASE_DIR, 'templates', 'chords.js')
if os.path.exists(chords_input): shutil.copy2(chords_input, os.path.join(BASE_DIR, 'public', 'chords.js'))

setlist_input = os.path.join(BASE_DIR, 'templates', 'setlist.html')
if os.path.exists(setlist_input): shutil.copy2(setlist_input, os.path.join(BASE_DIR, 'public', 'setlist.html'))

bible_input = os.path.join(BASE_DIR, 'templates', 'bible.html')
if os.path.exists(bible_input): shutil.copy2(bible_input, os.path.join(BASE_DIR, 'public', 'bible.html'))

bible_books_input = os.path.join(BASE_DIR, 'templates', 'bible_books_data.json')
if os.path.exists(bible_books_input): shutil.copy2(bible_books_input, os.path.join(BASE_DIR, 'public', 'bible_books_data.json'))

with open(template_path, 'r', encoding='utf-8') as f:
    master_template = f.read()

master_template = master_template.replace('href="style.css"', 'href="../style.css"')
master_template = master_template.replace('href="request.html"', 'href="../request.html"')
master_template = master_template.replace('href="bible.html"', 'href="../bible.html"')
master_template = master_template.replace('href="setlist.html"', 'href="../setlist.html"')
master_template = master_template.replace('href="/"', 'href="../index.html"')

def detect_language(text_to_check, lyrics_text=""):
    text_to_check = text_to_check.lower()
    if "malayalam" in text_to_check or "manglish" in text_to_check or any('\u0D00' <= c <= '\u0D7F' for c in lyrics_text):
        return "malayalam"
    elif "hindi" in text_to_check or "hinglish" in text_to_check or any('\u0900' <= c <= '\u097F' for c in lyrics_text):
        return "hindi"
    return "english"

def classify_song(title, author, lyrics, meaning):
    text_corpus = f"{title} {author} {lyrics} {meaning}".lower()
    
    # 1. Vibes
    vibes = []
    if re.search(r'\b(dance|dancing|shout|rejoice|joy|joyful|celebrate|celebration|clapping|sing aloud|gladness|cheerful|upbeat|fast|tempo|praise the lord|praise him|exalt|hallelujah)\b', text_corpus):
        vibes.append('upbeat')
    if re.search(r'\b(peace|peaceful|quiet|still|stillness|rest|comfort|weary|shelter|tears|solace|calm|gentle|refuge|haven|safe)\b', text_corpus):
        vibes.append('peaceful')
    if re.search(r'\b(battle|victory|victorious|conqueror|overcome|overcoming|chains|breakthrough|enemy|warfare|army|fight|stronghold|mighty warrior|triumph)\b', text_corpus):
        vibes.append('warfare')
    if re.search(r'\b(holy|worthy|bow down|adoration|awe|majesty|reverence|intimate|intimacy|surrender|throne|glory|presence|hallowed)\b', text_corpus):
        vibes.append('deep-worship')
    if not vibes:
        vibes.append('worship')

    # 2. Biblical Themes
    themes = []
    if re.search(r'\b(grace|mercy|unmerited|forgiven|forgiveness|kripa|compassion|cleansed)\b', text_corpus):
        themes.append('grace')
    if re.search(r'\b(cross|calvary|crucified|crucifixion|blood of jesus|lamb of god|resurrection|risen|tomb|redeemed|redemption|atonement|nails)\b', text_corpus):
        themes.append('the-cross')
    if re.search(r'\b(heal|healing|healer|sickness|disease|restored|restoration|wounds|cure|brokenhearted|changa)\b', text_corpus):
        themes.append('healing')
    if re.search(r'\b(holy spirit|spirit of god|anointing|fire fall|pentecost|comforter|ruach|pavitra aatma)\b', text_corpus):
        themes.append('holy-spirit')
    if re.search(r'\b(faith|trust|believe|assurance|unshakable|standing firm|faithful|faithfulness|visvasam|bharosa)\b', text_corpus):
        themes.append('faith')
    if re.search(r'\b(surrender|i give you my heart|take my life|all to jesus|consecrate|offering|my all)\b', text_corpus):
        themes.append('surrender')

    # 3. Specific Scripture Citations
    scriptures = []
    if re.search(r'\b(psalm[s]?\s*23|shepherd|green pastures|valley of the shadow|still waters|cup runneth over)\b', text_corpus):
        scriptures.append('psalm-23')
    if re.search(r'\b(psalm[s]?\s*103|bless the lord o my soul|forget not all his benefits)\b', text_corpus):
        scriptures.append('psalm-103')
    if re.search(r'\b(psalm[s]?\s*91|shadow of the almighty|refuge and fortress|under his wings|no evil shall befall)\b', text_corpus):
        scriptures.append('psalm-91')
    if re.search(r'\b(psalm[s]?\s*46|be still and know|refuge and strength|though the earth give way)\b', text_corpus):
        scriptures.append('psalm-46')
    if re.search(r'\b(romans\s*8|more than conquerors|no condemnation|who shall separate us)\b', text_corpus):
        scriptures.append('romans-8')
    if re.search(r'\b(isaiah\s*53|by his stripes|pierced for our transgressions|man of sorrows)\b', text_corpus):
        scriptures.append('isaiah-53')
    if re.search(r'\b(john\s*3|for god so loved the world|everlasting life|born again)\b', text_corpus):
        scriptures.append('john-3')
    if re.search(r'\b(philippians\s*4|i can do all things through christ|peace that passes all understanding)\b', text_corpus):
        scriptures.append('philippians-4')

    # Primary badges for card UI
    primary_vibe_label = "🙏 Worship"
    if "upbeat" in vibes:
        primary_vibe_label = "⚡ Upbeat"
    elif "warfare" in vibes:
        primary_vibe_label = "⚔️ Warfare"
    elif "peaceful" in vibes:
        primary_vibe_label = "🌿 Peaceful"
    elif "deep-worship" in vibes:
        primary_vibe_label = "🕊️ Deep Worship"

    primary_theme_label = ""
    if "psalm-23" in scriptures:
        primary_theme_label = "🐑 Psalm 23"
    elif "psalm-103" in scriptures:
        primary_theme_label = "📖 Psalm 103"
    elif "romans-8" in scriptures:
        primary_theme_label = "📖 Romans 8"
    elif "john-3" in scriptures:
        primary_theme_label = "📖 John 3"
    elif "psalm-91" in scriptures:
        primary_theme_label = "📖 Psalm 91"
    elif "psalm-46" in scriptures:
        primary_theme_label = "📖 Psalm 46"
    elif "the-cross" in themes:
        primary_theme_label = "✝️ The Cross"
    elif "grace" in themes:
        primary_theme_label = "✨ Grace"
    elif "healing" in themes:
        primary_theme_label = "🩹 Healing"
    elif "holy-spirit" in themes:
        primary_theme_label = "🔥 Holy Spirit"
    elif "faith" in themes:
        primary_theme_label = "🛡️ Faith"
    elif "surrender" in themes:
        primary_theme_label = "🙌 Surrender"

    return vibes, themes, scriptures, primary_vibe_label, primary_theme_label

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
                vibes, themes, scriptures, primary_vibe_label, primary_theme_label = classify_song(title, author, lyrics_text, meaning_text)
                
                songs_data.append({
                    'title': title, 
                    'author': author, 
                    'meaning': meaning_text,
                    'apple_id': apple_id,
                    'lyrics': lyrics_text, 
                    'filename': filename.replace('.txt', '.html'),
                    'language': lang_attr,
                    'vibes': vibes,
                    'themes': themes,
                    'scriptures': scriptures,
                    'primary_vibe_label': primary_vibe_label,
                    'primary_theme_label': primary_theme_label
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
        'lyrics': song['lyrics'],
        'vibes': song['vibes'],
        'themes': song['themes'],
        'scriptures': song['scriptures'],
        'language': song['language']
    })
    
    if song['apple_id']:
        full_song_content += f'''
<div class="player-container">
    <iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="150" class="apple-iframe" sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation" src="https://embed.music.apple.com/us/album/-/1?i={song['apple_id']}"></iframe>
</div>
'''

    # Clean query for external streaming platforms
    c_title = re.sub(r'\|.*$', '', song['title'])
    c_title = re.sub(r'\((official|video|audio|lyric|visualizer|music video|lyric video|official audio|official video|cover|remix)[^)]*\)', '', c_title, flags=re.IGNORECASE)
    c_title = re.sub(r'\[(official|video|audio|lyric|visualizer|music video|lyric video|official audio|official video|cover|remix)[^\]]*\]', '', c_title, flags=re.IGNORECASE)
    c_title = c_title.replace('"', '').strip()
    
    c_author = re.sub(r'\|.*$', '', song['author'])
    c_author = re.sub(r'@\w+', '', c_author).strip()
    
    stream_query = urllib.parse.quote(f"{c_title} {c_author}".strip())
    
    spotify_url = f"https://open.spotify.com/search/{stream_query}"
    yt_music_url = f"https://music.youtube.com/search?q={stream_query}"
    youtube_url = f"https://www.youtube.com/results?search_query={stream_query}"
    amazon_music_url = f"https://music.amazon.com/search/{stream_query}"
    apple_music_url = f"https://music.apple.com/us/album/-/1?i={song['apple_id']}" if song['apple_id'] else f"https://music.apple.com/us/search?term={stream_query}"

    full_song_content += f'''
<div class="streaming-hub">
    <span class="streaming-hub-title">🎧 Stream on Your Preferred Platform</span>
    <div class="streaming-badges">
        <a href="{spotify_url}" target="_blank" rel="noopener noreferrer" class="stream-badge spotify" title="Listen on Spotify">
            <svg viewBox="0 0 24 24" class="stream-icon"><path fill="currentColor" d="M12 2C6.477 2 2 6.477 2 12c0 5.524 4.477 10 10 10s10-4.476 10-10c0-5.523-4.477-10-10-10zm4.587 14.428c-.18.295-.563.387-.857.208-2.35-1.434-5.308-1.758-8.793-.963-.335.077-.67-.133-.746-.468-.077-.334.132-.67.467-.746 3.808-.87 7.076-.496 9.721 1.112.294.18.388.563.208.857zm1.233-2.74c-.226.367-.706.482-1.072.257-2.687-1.652-6.785-2.131-9.965-1.166-.413.127-.849-.107-.975-.521-.127-.414.108-.849.522-.976 3.632-1.102 8.147-.568 11.233 1.332.366.227.482.707.257 1.074zm.105-2.835C14.692 8.95 9.375 8.775 6.297 9.71c-.494.15-1.016-.129-1.166-.624-.149-.495.13-1.016.625-1.166 3.532-1.073 9.404-.866 13.115 1.337.445.264.59.838.327 1.282-.264.443-.838.59-1.274.314z"/></svg>
            <span>Spotify</span>
        </a>
        <a href="{yt_music_url}" target="_blank" rel="noopener noreferrer" class="stream-badge yt-music" title="Listen on YouTube Music">
            <svg viewBox="0 0 24 24" class="stream-icon"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/><polygon fill="currentColor" points="10,8.5 16,12 10,15.5"/></svg>
            <span>YouTube Music</span>
        </a>
        <a href="{apple_music_url}" target="_blank" rel="noopener noreferrer" class="stream-badge apple-music" title="Listen on Apple Music">
            <svg viewBox="0 0 24 24" class="stream-icon"><path fill="currentColor" d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.62-.75 1.04-1.8 1.01-2.87-.96.04-2.12.64-2.81 1.45-.6.71-1.13 1.83-1 2.87 1.07.08 2.18-.7 2.8-1.45z"/></svg>
            <span>Apple Music</span>
        </a>
        <a href="{youtube_url}" target="_blank" rel="noopener noreferrer" class="stream-badge youtube" title="Watch on YouTube">
            <svg viewBox="0 0 24 24" class="stream-icon"><path fill="currentColor" d="M21.582 6.186c-.23-.86-.908-1.538-1.768-1.768C18.254 4 12 4 12 4s-6.254 0-7.814.418c-.86.23-1.538.908-1.768 1.768C2 7.746 2 12 2 12s0 4.254.418 5.814c.23.86.908 1.538 1.768 1.768C5.746 20 12 20 12 20s6.254 0 7.814-.418c.861-.23 1.538-.908 1.768-1.768C22 16.254 22 12 22 12s0-4.254-.418-5.814zM10 15.464V8.536L16 12l-6 3.464z"/></svg>
            <span>YouTube</span>
        </a>
        <a href="{amazon_music_url}" target="_blank" rel="noopener noreferrer" class="stream-badge amazon-music" title="Listen on Amazon Music">
            <svg viewBox="0 0 24 24" class="stream-icon"><path fill="currentColor" d="M13.9 14.5c-1.8 0-3.3-1.1-3.3-3.2 0-2.3 1.8-3.3 3.7-3.3 1 0 1.9.2 2.4.5v1.1c-.5-.3-1.2-.5-2.1-.5-1.2 0-2.1.6-2.1 1.8 0 1.1.7 1.8 2 1.8.8 0 1.6-.3 2.2-.6v1.1c-.7.5-1.7.7-2.8.7zm-1.8 4.4c-4.4 0-8.2-2.4-9.9-5.9-.2-.3 0-.7.3-.8.3-.1.7 0 .8.3 1.5 3.1 4.9 5.2 8.8 5.2 3.1 0 5.9-1.3 7.8-3.4.2-.3.6-.3.8-.1.3.2.3.6.1.8-2.1 2.4-5.3 3.9-8.7 3.9zm9.7-3.8c-.3-.4-1.7-.2-2.4-.1-.2 0-.3-.2-.2-.3.8-.9 2.2-.6 2.5-.2.3.4-.1 1.7-.8 2.4-.2.1-.3 0-.3-.2.2-.7.9-1.2 1.2-1.6z"/></svg>
            <span>Amazon Music</span>
        </a>
    </div>
</div>
'''
    # 2. INJECT PRESENTER VIEW & SETLIST BUTTONS
    safe_title = song['title'].replace("'", "\\'").replace('"', '&quot;')
    safe_author = song['author'].replace("'", "\\'").replace('"', '&quot;')
    full_song_content += f'''
<div style="margin-top: 25px; margin-bottom: 30px; display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
    <a href="../presenter.html?song={song['filename']}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; padding: 10px 22px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 0.92rem; transition: all 0.2s;">
        📺 Launch Presenter View
    </a>
    <button onclick="addToSundaySetlist('{song['filename']}', '{safe_title}', '{safe_author}')" id="btnSetlistAdd" style="display: inline-flex; align-items: center; gap: 8px; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; padding: 10px 22px; border-radius: 30px; font-weight: bold; font-size: 0.92rem; cursor: pointer; transition: all 0.2s;">
        📋 Add to Sunday Setlist
    </button>
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
    
    # Construct expanded search tokens and tags
    theme_aliases = []
    for t in song['themes']:
        if t == 'grace': theme_aliases.extend(['grace', 'mercy', 'forgiveness'])
        elif t == 'the-cross': theme_aliases.extend(['cross', 'calvary', 'resurrection'])
        elif t == 'healing': theme_aliases.extend(['heal', 'healing', 'healer', 'changa'])
        elif t == 'holy-spirit': theme_aliases.extend(['holy spirit', 'spirit', 'anointing'])
        elif t == 'faith': theme_aliases.extend(['faith', 'trust', 'faithful'])
        elif t == 'surrender': theme_aliases.extend(['surrender', 'consecration'])

    for s in song['scriptures']:
        if s == 'psalm-23': theme_aliases.extend(['psalm 23', 'psalm23', 'shepherd', 'psalms 23'])
        elif s == 'psalm-103': theme_aliases.extend(['psalm 103', 'psalm103', 'bless the lord', 'psalms 103'])
        elif s == 'psalm-91': theme_aliases.extend(['psalm 91', 'psalm91', 'refuge', 'fortress', 'psalms 91'])
        elif s == 'psalm-46': theme_aliases.extend(['psalm 46', 'psalm46', 'be still', 'psalms 46'])
        elif s == 'romans-8': theme_aliases.extend(['romans 8', 'romans8', 'conquerors', 'no condemnation'])
        elif s == 'isaiah-53': theme_aliases.extend(['isaiah 53', 'isaiah53', 'by his stripes'])
        elif s == 'john-3': theme_aliases.extend(['john 3', 'john3', 'john 3:16'])
        elif s == 'philippians-4': theme_aliases.extend(['philippians 4', 'philippians4', 'rejoice'])

    for v in song['vibes']:
        if v == 'upbeat': theme_aliases.extend(['upbeat', 'fast', 'praise', 'dance', 'joy'])
        elif v == 'peaceful': theme_aliases.extend(['peaceful', 'peace', 'quiet', 'rest', 'calm'])
        elif v == 'warfare': theme_aliases.extend(['warfare', 'battle', 'victory', 'anthem'])
        elif v == 'deep-worship': theme_aliases.extend(['deep worship', 'holy', 'majesty', 'awe'])

    searchable_blob = f"{song['title'].lower()} {song['author'].lower()} {' '.join(song['vibes'])} {' '.join(song['themes'])} {' '.join(song['scriptures'])} {' '.join(theme_aliases)}".replace('"', '&quot;')
    vibes_attr = ' '.join(song['vibes'])
    themes_attr = ' '.join(song['themes'])
    scrip_attr = ' '.join(song['scriptures'])
    theme_badge_html = f'<span class="tag tag-theme">{song["primary_theme_label"]}</span>' if song['primary_theme_label'] else ''

    lyrics_cards += f'''
    <a href="{song["filename"]}" class="song-card interactive-card" data-index="{i}" data-time="{creation_time}" data-sort-name="{clean_title}" data-language="{song["language"]}" data-vibe="{vibes_attr}" data-theme="{themes_attr}" data-scripture="{scrip_attr}" data-title="{searchable_blob}">
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
                    <span class="tag tag-vibe">{song["primary_vibe_label"]}</span>
                    {theme_badge_html}
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
        <input type="text" id="searchInput" placeholder="Search by Title, Artist, Vibe (e.g. 'upbeat grace'), or Scripture (e.g. 'Psalm 23')...">
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

    <!-- Vibe & Scripture Filter System -->
    <div class="vibe-filter-container">
        <!-- Vibe row -->
        <div class="filter-pills-row">
            <span class="filter-row-title">⚡ Vibe / Mood:</span>
            <div class="filter-pills-list" id="vibeFilterPills">
                <button type="button" class="filter-pill active" data-vibe="all">All Vibes</button>
                <button type="button" class="filter-pill" data-vibe="upbeat">⚡ Upbeat Praise</button>
                <button type="button" class="filter-pill" data-vibe="deep-worship">🕊️ Deep Worship</button>
                <button type="button" class="filter-pill" data-vibe="peaceful">🌿 Peaceful &amp; Rest</button>
                <button type="button" class="filter-pill" data-vibe="warfare">⚔️ Spiritual Warfare</button>
            </div>
        </div>
        
        <!-- Scripture & Theme row -->
        <div class="filter-pills-row">
            <span class="filter-row-title">📖 Scripture &amp; Theme:</span>
            <div class="filter-pills-list" id="themeFilterPills">
                <button type="button" class="filter-pill active" data-theme="all">All Themes</button>
                <button type="button" class="filter-pill" data-theme="grace">✨ Grace &amp; Mercy</button>
                <button type="button" class="filter-pill" data-theme="the-cross">✝️ The Cross</button>
                <button type="button" class="filter-pill" data-theme="healing">🩹 Healing</button>
                <button type="button" class="filter-pill" data-theme="holy-spirit">🔥 Holy Spirit</button>
                <button type="button" class="filter-pill" data-theme="faith">🛡️ Faith &amp; Trust</button>
                <button type="button" class="filter-pill pill-scripture" data-theme="psalm-23">🐑 Psalm 23</button>
                <button type="button" class="filter-pill pill-scripture" data-theme="psalm-103">📖 Psalm 103</button>
                <button type="button" class="filter-pill pill-scripture" data-theme="psalm-91">🏔️ Psalm 91</button>
                <button type="button" class="filter-pill pill-scripture" data-theme="romans-8">🕊️ Romans 8</button>
            </div>
        </div>
    </div>
    
    <div class="results-stats-row">
        <span id="resultsCount">Showing all songs</span>
        <button id="resetAllFilters" class="btn-reset-filters" style="display: none;">✕ Clear all filters</button>
    </div>
</div>

<div class="lyrics-grid" id="lyricsGrid">
    {lyrics_cards}
</div>

<script>
    let favorites = JSON.parse(localStorage.getItem('lyric_favorites')) || [];
    let currentSort = 'alphabetical';
    let currentVibe = 'all';
    let currentTheme = 'all';

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

    document.querySelectorAll('.sort-tab').forEach(tab => {{
        tab.addEventListener('click', function() {{
            document.querySelectorAll('.sort-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentSort = this.getAttribute('data-sort');
            filterItems();
        }});
    }});

    // Vibe pills setup
    document.querySelectorAll('#vibeFilterPills .filter-pill').forEach(pill => {{
        pill.addEventListener('click', function() {{
            document.querySelectorAll('#vibeFilterPills .filter-pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            currentVibe = this.getAttribute('data-vibe');
            filterItems();
        }});
    }});

    // Theme & Scripture pills setup
    document.querySelectorAll('#themeFilterPills .filter-pill').forEach(pill => {{
        pill.addEventListener('click', function() {{
            document.querySelectorAll('#themeFilterPills .filter-pill').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            currentTheme = this.getAttribute('data-theme');
            filterItems();
        }});
    }});

    // Reset button setup
    let resetBtn = document.getElementById('resetAllFilters');
    if (resetBtn) {{
        resetBtn.addEventListener('click', function() {{
            document.getElementById('searchInput').value = '';
            document.getElementById('langFilter').value = 'all';
            currentVibe = 'all';
            currentTheme = 'all';
            document.querySelectorAll('#vibeFilterPills .filter-pill').forEach(p => {{
                p.classList.toggle('active', p.getAttribute('data-vibe') === 'all');
            }});
            document.querySelectorAll('#themeFilterPills .filter-pill').forEach(p => {{
                p.classList.toggle('active', p.getAttribute('data-theme') === 'all');
            }});
            filterItems();
        }});
    }}

    function filterItems() {{
        let rawSearch = document.getElementById('searchInput').value.toLowerCase().trim();
        let selectedLang = document.getElementById('langFilter').value;
        let cards = Array.from(document.getElementsByClassName('interactive-card'));
        let grid = document.getElementById('lyricsGrid');
        let resultsCount = document.getElementById('resultsCount');
        let resetBtn = document.getElementById('resetAllFilters');
        
        // Clean natural language conversational phrases
        let cleaned = rawSearch
            .replace(/\\b(songs?\\s+about|songs?\\s+on|songs?\\s+based\\s+on|songs?\\s+for|hymns?\\s+about|hymns?\\s+on|music\\s+about|worship\\s+songs?\\s+about|tracks?\\s+about)\\b/gi, ' ')
            .replace(/[^\\w\\s-]/g, ' ')
            .trim();
        
        let searchTerms = cleaned.split(/\\s+/).filter(t => t.length > 0 && !['and', 'the', 'in', 'of', 'to', 'a', 'an', 'is'].includes(t));
        let visibleCount = 0;
        
        cards.forEach(card => {{
            let searchableText = card.getAttribute('data-title') || '';
            let cardLang = card.getAttribute('data-language') || '';
            let cardVibes = (card.getAttribute('data-vibe') || '').split(' ');
            let cardThemes = (card.getAttribute('data-theme') || '').split(' ');
            let cardScriptures = (card.getAttribute('data-scripture') || '').split(' ');
            
            let heartIcon = card.querySelector('.heart-icon');
            let songId = heartIcon ? heartIcon.getAttribute('data-id') : null;
            
            let matchesSearch = true;
            if (searchTerms.length > 0) {{
                matchesSearch = searchTerms.every(term => searchableText.includes(term));
            }}
            let matchesLang = (selectedLang === 'all' || cardLang === selectedLang);
            let matchesFav = (currentSort !== 'favorites' || (songId && favorites.includes(songId)));
            let matchesVibe = (currentVibe === 'all' || cardVibes.includes(currentVibe));
            let matchesTheme = (currentTheme === 'all' || cardThemes.includes(currentTheme) || cardScriptures.includes(currentTheme));
            
            let isVisible = matchesSearch && matchesLang && matchesFav && matchesVibe && matchesTheme;
            card.style.display = isVisible ? 'flex' : 'none';
            if (isVisible) visibleCount++;
        }});

        let hasFilter = (rawSearch !== '' || selectedLang !== 'all' || currentVibe !== 'all' || currentTheme !== 'all' || currentSort === 'favorites');
        if (resetBtn) resetBtn.style.display = hasFilter ? 'inline-block' : 'none';
        if (resultsCount) {{
            if (!hasFilter) {{
                resultsCount.textContent = 'Showing all ' + visibleCount + ' songs';
            }} else {{
                resultsCount.textContent = 'Found ' + visibleCount + ' matching song' + (visibleCount === 1 ? '' : 's');
            }}
        }}
        
        if (currentSort === 'alphabetical') {{
            cards.sort((a, b) => a.getAttribute('data-sort-name').localeCompare(b.getAttribute('data-sort-name')));
        }} else if (currentSort === 'recent') {{
            cards.sort((a, b) => parseFloat(b.getAttribute('data-time')) - parseFloat(a.getAttribute('data-time')));
        }} else {{
            cards.sort((a, b) => parseInt(a.getAttribute('data-index')) - parseInt(b.getAttribute('data-index')));
        }}
        
        cards.forEach(card => grid.appendChild(card));
    }}

    // Check URL parameters on load (e.g. ?theme=grace or ?theme=psalm-23 or ?vibe=upbeat)
    let urlParams = new URLSearchParams(window.location.search);
    let urlVibe = urlParams.get('vibe');
    let urlTheme = urlParams.get('theme') || urlParams.get('scripture');
    let urlQuery = urlParams.get('q');
    let urlLang = urlParams.get('lang');

    if (urlQuery) {{
        document.getElementById('searchInput').value = urlQuery;
    }}
    if (urlLang) {{
        document.getElementById('langFilter').value = urlLang;
    }}
    if (urlVibe) {{
        let matchingPill = document.querySelector('#vibeFilterPills .filter-pill[data-vibe="' + urlVibe + '"]');
        if (matchingPill) {{
            document.querySelectorAll('#vibeFilterPills .filter-pill').forEach(p => p.classList.remove('active'));
            matchingPill.classList.add('active');
            currentVibe = urlVibe;
        }}
    }}
    if (urlTheme) {{
        let matchingPill = document.querySelector('#themeFilterPills .filter-pill[data-theme="' + urlTheme + '"]');
        if (matchingPill) {{
            document.querySelectorAll('#themeFilterPills .filter-pill').forEach(p => p.classList.remove('active'));
            matchingPill.classList.add('active');
            currentTheme = urlTheme;
        }}
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
<div class="homepage-hero-wrapper" style="text-align: center; padding: 40px 20px 30px; margin-bottom: 25px;">
    <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; padding: 6px 18px; border-radius: 30px; font-size: 0.88rem; font-weight: 700; margin-bottom: 18px;">
        🕊️ Free • Ad-Free • Built for the Kingdom of God
    </div>
    
    <h2 style="font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 800; line-height: 1.25; margin-bottom: 14px; color: var(--header-title); font-family: var(--ui-font);">
        Your Complete Christian Worship &amp; Church Tech Hub
    </h2>
    
    <p style="font-size: clamp(0.95rem, 1.8vw, 1.15rem); color: var(--text-muted); max-width: 800px; margin: 0 auto 28px; line-height: 1.6;">
        Empowering worship leaders, church media teams, musicians, and believers everywhere. Explore 660+ verified song lyrics with theological roots, multi-lingual Holy Scriptures, church slide projection, Sunday setlist planning, and OBS livestream overlays.
    </p>

    <!-- Quick Navigation Hub Pills -->
    <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-bottom: 25px;">
        <a href="lyrics-archive/index.html" class="btn-primary" style="padding: 12px 22px; font-size: 0.95rem; font-weight: 700; border-radius: 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
            📖 Explore 660+ Lyrics
        </a>
        <a href="bible.html" class="btn-primary" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; padding: 12px 22px; font-size: 0.95rem; font-weight: 700; border-radius: 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
            ✝️ Holy Bible Hub
        </a>
        <a href="setlist.html" class="btn-primary" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; padding: 12px 22px; font-size: 0.95rem; font-weight: 700; border-radius: 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
            📋 Sunday Setlist Builder
        </a>
        <a href="karaoke-tracks/index.html" class="btn-primary" style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); color: #c084fc; padding: 12px 22px; font-size: 0.95rem; font-weight: 700; border-radius: 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;">
            🎤 Worship Karaokes
        </a>
    </div>

    <!-- Quick Vibe & Scripture Finder Row -->
    <div style="margin-top: 15px; margin-bottom: 10px; text-align: center;">
        <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.75px; color: var(--text-muted); margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span>🔍 Search Songs by Vibe &amp; Scripture:</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-width: 860px; margin: 0 auto;">
            <a href="lyrics-archive/index.html?theme=grace" class="quick-vibe-pill">✨ Grace &amp; Mercy</a>
            <a href="lyrics-archive/index.html?theme=psalm-23" class="quick-vibe-pill">🐑 Psalm 23</a>
            <a href="lyrics-archive/index.html?vibe=upbeat" class="quick-vibe-pill">⚡ Upbeat Praise</a>
            <a href="lyrics-archive/index.html?vibe=deep-worship" class="quick-vibe-pill">🕊️ Deep Worship</a>
            <a href="lyrics-archive/index.html?theme=the-cross" class="quick-vibe-pill">✝️ The Cross</a>
            <a href="lyrics-archive/index.html?theme=healing" class="quick-vibe-pill">🩹 Healing</a>
            <a href="lyrics-archive/index.html?theme=faith" class="quick-vibe-pill">🛡️ Faith &amp; Trust</a>
            <a href="lyrics-archive/index.html?theme=psalm-103" class="quick-vibe-pill">📖 Psalm 103</a>
            <a href="lyrics-archive/index.html?theme=romans-8" class="quick-vibe-pill">🕊️ Romans 8</a>
        </div>
    </div>
</div>

<!-- Section: What We Offer -->
<div class="glass-search-container" style="padding: 35px 25px; margin-bottom: 40px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="font-size: 1.85rem; font-weight: 800; color: var(--header-title); margin-bottom: 8px;">
            ✨ What Our Website Offers
        </h2>
        <p style="color: var(--text-muted); font-size: 1rem; max-width: 650px; margin: 0 auto;">
            Everything you need for personal devotion, worship team rehearsals, and church services in one place.
        </p>
    </div>

    <div class="lyrics-grid" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px;">
        <!-- Card 1 -->
        <a href="lyrics-archive/index.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">📖</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">660+ Verified Song Lyrics</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Extensive worship catalog spanning English, Malayalam, Hindi, Manglish, and Hinglish with on-site streaming on Apple Music, Spotify, YouTube & Amazon Music.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #38bdf8; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Explore Library →
            </span>
        </a>

        <!-- Card 2 -->
        <a href="bible.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">✝️</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Multi-Lingual Holy Bible</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Read scripture across 9 translations including BSB (Modern), KJV 1769, Malayalam (സത്യവേദപുസ്തകം), Hindi (पवित्र बाइबिल), and Tamil with side-by-side parallel mode.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #38bdf8; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Read Scripture →
            </span>
        </a>

        <!-- Card 3 -->
        <a href="presenter.html" target="_blank" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">📺</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Live Church Presenter</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                ProPresenter-style live projection tool. Features 4-line smart verse slides, digital service clock, watermark, blackout mode (B), slide grid overview (G), and themes.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #fbbf24; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Launch Presenter →
            </span>
        </a>

        <!-- Card 4 -->
        <a href="setlist.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">📋</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Sunday Setlist Builder</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Assemble your Sunday worship flow in minutes. Choose custom song keys, assign lead vocalists, add transition cues, and launch the entire service into Presenter View.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #fbbf24; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Plan Service →
            </span>
        </a>

        <!-- Card 5 -->
        <a href="presenter.html?mode=lower-third" target="_blank" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">📡</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">OBS &amp; Livestream Overlays</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Broadcast-ready transparent lower-third overlays for OBS Studio and vMix. Synchronizes live in real-time (0ms latency) with the worship presenter on your laptop.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #38bdf8; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Open OBS Source →
            </span>
        </a>

        <!-- Card 6 -->
        <a href="karaoke-tracks/index.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">🎤</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Worship Karaokes &amp; Backing</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                High-definition instrumental tracks and worship karaokes. Ideal for choir practice, youth fellowships, home church gatherings, and vocal rehearsals.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #c084fc; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Sing Worship →
            </span>
        </a>

        <!-- Card 7 -->
        <a href="lyrics-archive/index.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">💡</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Theological Song Meanings</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Biblical reflections and theological backgrounds for each worship song to help praise teams and congregations worship with spiritual understanding.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #38bdf8; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Learn Meanings →
            </span>
        </a>

        <!-- Card 8 -->
        <a href="request.html" class="song-card interactive-card" style="display: flex; flex-direction: column; padding: 26px 20px; text-decoration: none; border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 12px;">💌</div>
            <h3 class="card-title" style="font-size: 1.18rem; margin-bottom: 8px; color: var(--header-title);">Instant Song Request Desk</h3>
            <p class="card-subtitle" style="font-size: 0.88rem; white-space: normal; line-height: 1.55; color: var(--text-muted);">
                Can't find a rare hymn or local release? Submit a request and our team gets notified instantly via Telegram bot to add it to the platform.
            </p>
            <span style="margin-top: auto; padding-top: 14px; color: #38bdf8; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 4px;">
                Request a Song →
            </span>
        </a>
    </div>
</div>
'''

home_html = root_template.replace('{{TITLE}}', 'Christian Worship & Ministry Hub')\
                         .replace('{{ARTIST}}', '660+ Verified Song Lyrics, Multi-Lingual Bible, Live Presenter & Sunday Service Setlists')\
                         .replace('{{CATEGORY}}', 'Worship Portal')\
                         .replace('{{LYRICS_CONTENT}}', home_content)\
                         .replace('{{BACK_URL}}', '#')\
                         .replace('{{BACK_TEXT}}', 'Welcome to the Platform')
                         
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

for path in ["", "request.html", "bible.html", "setlist.html", "lyrics-archive/index.html", "karaoke-tracks/index.html", "coming-soon.html", "presenter.html"]:
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