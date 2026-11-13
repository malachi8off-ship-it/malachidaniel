import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Try importing Google GenAI for Vision OCR & Contextualization
try:
    from google import genai
    from PIL import Image
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_LYRICS_DIR = os.path.join(BASE_DIR, 'raw_lyrics')
os.makedirs(RAW_LYRICS_DIR, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai_client = None
if HAS_GENAI and GEMINI_API_KEY:
    try:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        genai_client = None

# ANSI Color Codes for terminal UI
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def get_existing_slugs():
    existing = set()
    for f in os.listdir(RAW_LYRICS_DIR):
        if f.endswith('.txt'):
            existing.add(f.replace('.txt', '').lower())
    return existing

def clean_madely_section(raw_text):
    lines = [l.strip() for l in raw_text.splitlines()]
    cleaned = []
    skip_headers = {
        'malayalam lyrics', 'manglish lyrics', 'my notes', 'a', '|', 
        'media', 'loading...', 'share', 'print', 'slideshow', 'download'
    }
    for l in lines:
        if not l or l.lower() in skip_headers:
            continue
        # Strip choir tags (M, F, A, 🔔, dashes)
        l = re.sub(r'^(M|F|A)\s*$', '', l)
        l = re.sub(r'[🔔\u2014\u2013\-]{2,}', '', l).strip()
        if l and (not cleaned or l != cleaned[-1]):
            cleaned.append(l)
    return '\n'.join(cleaned)

def search_madely(query):
    """Searches madely.us for Malayalam & Manglish Christian lyrics."""
    url = f"https://madely.us/?s={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/lyrics/' in href and href != 'https://madely.us/lyrics/' and not href.endswith('#respond'):
                    text = a.get_text(strip=True)
                    if text and text not in ['Open Song Lyrics ->>', 'No comments yet', 'Home', 'Lyrics'] and not re.match(r'^[A-Za-z]+\s+\d+,\s+\d{4}$', text):
                        if not any(r['url'] == href for r in results):
                            results.append({'title': text, 'url': href})
    except Exception as e:
        print(f"{RED}Error querying madely.us: {e}{RESET}")
    return results

def fetch_madely_song(url):
    """Fetches song page and extracts clean Malayalam and Manglish lyrics."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            soup = BeautifulSoup(resp.read().decode('utf-8'), 'html.parser')
            
            # Title
            title = ''
            title_tag = soup.find('h1') or soup.find('h2', class_='entry-title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                title = re.sub(r'\s*(Malayalam|Manglish|Song\s+Lyrics|Lyrics|\-|\–|MADELY).*$', '', title, flags=re.IGNORECASE).strip()
            
            sections = soup.find_all('section')
            malayalam_text = ''
            manglish_text = ''
            
            if len(sections) >= 1:
                malayalam_text = clean_madely_section(sections[0].get_text(separator='\n'))
            if len(sections) >= 2:
                manglish_text = clean_madely_section(sections[1].get_text(separator='\n'))
                
            return {
                'title': title,
                'malayalam': malayalam_text,
                'manglish': manglish_text,
                'url': url
            }
    except Exception as e:
        print(f"{RED}Error fetching song page: {e}{RESET}")
        return None

def fetch_itunes_track_id(title, artist=""):
    """Fetches Apple Music Track ID via iTunes Search API."""
    try:
        clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title).strip()
        query = f"{clean_title} {artist}".strip()
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('resultCount', 0) > 0:
                track = data['results'][0]
                return str(track.get('trackId', 'NONE'))
    except Exception:
        pass
    return "NONE"

def generate_ai_meaning(title, artist, lyrics):
    """Generates theological meaning summary using Gemini."""
    if not genai_client:
        return ""
    try:
        prompt = (
            f"Analyze this Christian worship song: Title: '{title}', Artist: '{artist}'.\n"
            f"Lyrics snippet:\n{lyrics[:800]}\n\n"
            "Provide a concise 2-3 sentence theological reflection of this song. "
            "Highlight the core biblical message, references (such as specific Psalms or Gospels if applicable), "
            "and theme (Grace, Cross, Worship, Healing, etc.). Do not include markdown headers or bullet points."
        )
        resp = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        if resp and resp.text:
            return resp.text.strip().replace('\n', ' ')
    except Exception as e:
        print(f"{DIM}Note: AI meaning skipped: {e}{RESET}")
    return ""

def ocr_lyrics_from_image(image_path):
    """Extracts lyrics from a photo/screenshot using Gemini Vision."""
    if not genai_client:
        print(f"{RED}Gemini API is not available or GEMINI_API_KEY is missing in .env!{RESET}")
        return None
    
    if not os.path.exists(image_path):
        print(f"{RED}Image file not found: {image_path}{RESET}")
        return None

    try:
        img = Image.open(image_path)
        print(f"{CYAN}🔍 Analyzing image with Gemini Vision OCR...{RESET}")
        prompt = (
            "You are a Christian worship lyrics transcription specialist. "
            "Extract the song lyrics from this image. Return pure JSON with these exact keys:\n"
            "{\n"
            '  "title": "Song Title",\n'
            '  "artist": "Artist or Traditional",\n'
            '  "lyrics": "The full clean lyrics with proper stanzas...",\n'
            '  "language": "malayalam" or "hindi" or "english"\n'
            "}\n"
            "Preserve Malayalam or Devanagari Hindi script accurately. If it is Romanized/Manglish/Hinglish, keep it. "
            "Do not output markdown code blocks (```json)."
        )
        resp = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        text = resp.text.strip()
        # Clean potential markdown wrapping
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"{RED}OCR Failed: {e}{RESET}")
        return None

def save_song_to_archive(title, artist, lyrics_body, apple_id="NONE", meaning=""):
    """Saves song into raw_lyrics in standard format."""
    slug = slugify(f"{title}-{artist}")
    filename = f"{slug}.txt"
    filepath = os.path.join(RAW_LYRICS_DIR, filename)
    
    # Avoid overwriting without notice
    if os.path.exists(filepath):
        print(f"{YELLOW}⚠️ Song already exists at {filename}! Overwrite? (y/N): {RESET}", end="")
        if input().strip().lower() != 'y':
            print(f"{DIM}Skipped saving.{RESET}")
            return False

    content = (
        f"{title}\n"
        f"{artist}\n"
        f"meaning\n"
        f"{meaning}\n"
        f"apple_data\n"
        f"{apple_id}\n"
        f"lyrics\n"
        f"{lyrics_body}\n"
    )
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"{GREEN}✅ Saved successfully to: {BOLD}raw_lyrics/{filename}{RESET}")
    return True

def prompt_and_review_song(title, artist, malayalam_lyrics, manglish_lyrics="", default_meaning=""):
    """Interactive human review terminal prompt."""
    print("\n" + "="*70)
    print(f"{BOLD}{CYAN}🎵 SONG PREVIEW & REVIEW{RESET}")
    print("="*70)
    print(f"{BOLD}Title:{RESET}  {title}")
    print(f"{BOLD}Artist:{RESET} {artist}")
    
    # Determine lyrics body
    if malayalam_lyrics and manglish_lyrics:
        lyrics_body = f"[Malayalam]\n{malayalam_lyrics}\n\n[Manglish]\n{manglish_lyrics}"
    elif malayalam_lyrics:
        lyrics_body = malayalam_lyrics
    else:
        lyrics_body = manglish_lyrics
        
    print(f"\n{BOLD}{YELLOW}--- LYRICS PREVIEW (First 10 Lines) ---{RESET}")
    preview_lines = lyrics_body.splitlines()[:12]
    for l in preview_lines:
        print(f"  {l}")
    if len(lyrics_body.splitlines()) > 12:
        print(f"  {DIM}... ({len(lyrics_body.splitlines()) - 12} more lines){RESET}")
        
    print("\n" + "-"*70)
    print(f"Actions: [{BOLD}y{RESET}] Add Song  |  [{BOLD}n{RESET}] Skip  |  [{BOLD}v{RESET}] View Full Lyrics  |  [{BOLD}e{RESET}] Edit Details  |  [{BOLD}q{RESET}] Back")
    
    current_title = title
    current_artist = artist
    
    while True:
        choice = input(f"{BOLD}Your choice: {RESET}").strip().lower()
        if choice == 'y':
            print(f"{CYAN}🔍 Querying Apple Music Track ID...{RESET}")
            apple_id = fetch_itunes_track_id(current_title, current_artist)
            print(f"   Apple Track ID: {apple_id}")
            
            print(f"{CYAN}✨ Generating Theological Meaning & Context...{RESET}")
            meaning = generate_ai_meaning(current_title, current_artist, lyrics_body)
            if meaning:
                print(f"   Meaning: {meaning[:100]}...")
                
            saved = save_song_to_archive(current_title, current_artist, lyrics_body, apple_id, meaning)
            return saved
        elif choice == 'v':
            print("\n" + "="*70)
            print(f"{BOLD}FULL LYRICS:{RESET}")
            print(lyrics_body)
            print("="*70)
        elif choice == 'e':
            new_title = input(f"Enter Title [{current_title}]: ").strip()
            if new_title: current_title = new_title
            new_artist = input(f"Enter Artist [{current_artist}]: ").strip()
            if new_artist: current_artist = new_artist
            print(f"{GREEN}Updated: {current_title} by {current_artist}{RESET}")
        elif choice in ('n', 'q', ''):
            print(f"{DIM}Skipped.{RESET}")
            return False
        else:
            print("Invalid input. Type y, n, v, e, or q.")

def run_madely_search_flow():
    print(f"\n{BOLD}{CYAN}🔍 SEARCH MALAYALAM & MANGLISH SONGS (madely.us){RESET}")
    print(f"{DIM}You can search by song name, English transliteration, or lyric line (e.g. 'Sneham', 'Aalayil', 'Yahovaye').{RESET}")
    query = input(f"{BOLD}Enter search term: {RESET}").strip()
    if not query:
        return
        
    print(f"{CYAN}Searching madely.us for '{query}'...{RESET}")
    results = search_madely(query)
    
    if not results:
        print(f"{YELLOW}No songs found on madely.us for '{query}'.{RESET}")
        return
        
    print(f"\n{GREEN}Found {len(results)} songs:{RESET}")
    existing = get_existing_slugs()
    
    for idx, r in enumerate(results[:15], 1):
        slug_check = slugify(r['title'])
        status_tag = f"{DIM}[Already on site]{RESET}" if any(slug_check in s for s in existing) else f"{GREEN}[New]{RESET}"
        print(f"  {BOLD}{idx}.{RESET} {r['title']} {status_tag}")
        
    while True:
        sel = input(f"\nSelect song number to inspect (1-{min(len(results), 15)}, or 'q' to return): ").strip()
        if sel.lower() == 'q' or not sel:
            break
        if sel.isdigit() and 1 <= int(sel) <= min(len(results), 15):
            chosen = results[int(sel) - 1]
            print(f"{CYAN}Fetching {chosen['title']}...{RESET}")
            song = fetch_madely_song(chosen['url'])
            if song:
                prompt_and_review_song(
                    title=song['title'] or chosen['title'],
                    artist="Malayalam Worship",
                    malayalam_lyrics=song['malayalam'],
                    manglish_lyrics=song['manglish']
                )
            break
        else:
            print("Please enter a valid number.")

def run_hindi_worship_flow():
    print(f"\n{BOLD}{CYAN}🇮🇳 HINDI CHRISTIAN WORSHIP CURATOR{RESET}")
    print(f"{DIM}Search for popular Hindi worship songs (Yeshua Ministries, Bridge Music, Amit Kamble, Sheldon Bangera, etc.){RESET}")
    query = input(f"{BOLD}Enter Hindi song title or lyric line: {RESET}").strip()
    if not query:
        return
        
    if not genai_client:
        print(f"{RED}Gemini API client not available. Cannot fetch Hindi lyrics dynamically.{RESET}")
        return
        
    print(f"{CYAN}🔍 Finding verified lyrics for '{query}'...{RESET}")
    prompt = (
        f"Find the authentic Christian worship song lyrics for: '{query}'.\n"
        "Return pure JSON with this schema:\n"
        "{\n"
        '  "title": "Song Title",\n'
        '  "artist": "Artist or Ministry Name",\n'
        '  "hindi": "Lyrics in Devanagari Hindi...",\n'
        '  "hinglish": "Lyrics in Romanized Hinglish (English alphabet)...",\n'
        '  "meaning": "2 sentence biblical context and theme"\n'
        "}\n"
        "Do not include markdown codeblocks (```json)."
    )
    try:
        resp = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = resp.text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text).strip()
        data = json.loads(text)
        
        hindi_text = data.get('hindi', '').strip()
        hinglish_text = data.get('hinglish', '').strip()
        
        prompt_and_review_song(
            title=data.get('title', query),
            artist=data.get('artist', 'Hindi Worship'),
            malayalam_lyrics=hindi_text,
            manglish_lyrics=hinglish_text,
            default_meaning=data.get('meaning', '')
        )
    except Exception as e:
        print(f"{RED}Error retrieving Hindi worship song: {e}{RESET}")

def run_ocr_image_flow():
    print(f"\n{BOLD}{CYAN}📸 IMAGE-TO-TEXT WORSHIP LYRICS (VISION OCR){RESET}")
    print(f"{DIM}Extract lyrics from a screenshot, photo of a songbook, or WhatsApp graphic.{RESET}")
    path = input(f"{BOLD}Enter image path (or drag and drop file here): {RESET}").strip().strip('"').strip("'")
    if not path:
        return
        
    data = ocr_lyrics_from_image(path)
    if data:
        prompt_and_review_song(
            title=data.get('title', 'Unknown Title'),
            artist=data.get('artist', 'Worship Leader'),
            malayalam_lyrics=data.get('lyrics', '')
        )

def run_rebuild():
    print(f"\n{CYAN}🔨 Rebuilding malachidaniel.com static files with generator.py...{RESET}")
    os.system(f'"{sys.executable}" generator.py')

def main_menu():
    while True:
        print("\n" + "="*70)
        print(f"{BOLD}{GREEN}🕊️  MALACHI DANIEL — WORSHIP SONG CURATOR & INGESTION BOT{RESET}")
        print("="*70)
        print(f" {BOLD}[1]{RESET} 🔍 Search & Add Malayalam Songs ({CYAN}madely.us{RESET} — 8,200+ songs)")
        print(f" {BOLD}[2]{RESET} 🇮🇳 Search & Add Hindi Christian Worship Songs")
        print(f" {BOLD}[3]{RESET} 📸 Extract Lyrics from Image / Screenshot ({YELLOW}Gemini Vision OCR{RESET})")
        print(f" {BOLD}[4]{RESET} 🔨 Rebuild Website Now ({CYAN}generator.py{RESET})")
        print(f" {BOLD}[5]{RESET} ❌ Exit")
        print("="*70)
        
        choice = input(f"{BOLD}Select an option (1-5): {RESET}").strip()
        if choice == '1':
            run_madely_search_flow()
        elif choice == '2':
            run_hindi_worship_flow()
        elif choice == '3':
            run_ocr_image_flow()
        elif choice == '4':
            run_rebuild()
        elif choice in ('5', 'q', 'exit'):
            print(f"{GREEN}God bless your worship ministry! Goodbye.{RESET}")
            break
        else:
            print("Please select a valid option (1-5).")

if __name__ == '__main__':
    main_menu()
