import os
import requests
import re
import time
from omni_fetcher import (
    fetch_from_lrclib,
    fix_spelling_with_ai,
    fetch_via_ddg_scraper,
    save_lyrics,
    slugify,
    OUTPUT_DIR
)

# --- CONFIGURATION ---
# Add your favorite or regional worship artists to auto-sweep their top tracks
FEATURED_ARTISTS = [
    "Yeshua Ministries",
    "Bridge Music",
    "Sheldon Bangera",
    "Hillsong Worship",
    "Elevation Worship",
    "Maverick City Music",
    "Kari Jobe",
    "Matt Redman",
    "Forrest Frank",
    "Brandon Lake",
    "Casting Crowns",
    "MercyMe",
    "Skillet",
    "Lauren Daigle",
    "TobyMac",
    "For King & Country",
    "Anne Wilson",
    "Phil Wickham",
    "Seph Schlueter",
    "Katy Nichole",
    "Newsboys",
    "Zach Williams",
    "Toby Mac",
    "Tenth Ave North",
    "Steven Curtis Chapman",
    "Michael w smith",
    "Benjamin William Hastings",
    "Joy Williams",
    "Josiah Queen",
    "Third Day",
    "Jars of Clay",
    "Ankur Masih"
    "Nations of Worship",
    "Bridge Music",
    "Yeshua Ministries",
    "Joseph O'Brien"
    "Haddon"
]

def get_existing_slugs():
    """Returns a set of all slugified filenames currently in raw_lyrics/."""
    existing = set()
    if os.path.exists(OUTPUT_DIR):
        for fname in os.listdir(OUTPUT_DIR):
            if fname.endswith('.txt'):
                existing.add(fname.replace('.txt', ''))
    return existing

def discover_from_itunes_charts():
    """Fetches the current Top 100 Christian & Gospel songs from iTunes RSS."""
    print("\n📊 Fetching iTunes Top Christian & Gospel Charts...")
    url = "https://itunes.apple.com/us/rss/topsongs/limit=100/genre=22/json"
    discovered = []
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            entries = data.get('feed', {}).get('entry', [])
            for entry in entries:
                title = entry.get('im:name', {}).get('label', '')
                artist = entry.get('im:artist', {}).get('label', '')
                
                # Clean up title extras like "(Live)" or "[Feat. ...]"
                clean_title = re.sub(r'\(.*?\)|\[.*?\]', '', title).strip()
                if clean_title and artist:
                    discovered.append({'title': clean_title, 'artist': artist})
            print(f"✅ Retrieved {len(discovered)} songs from iTunes Charts.")
    except Exception as e:
        print(f"❌ Error fetching iTunes charts: {e}")
        
    return discovered

def discover_from_artist_sweep(artist_name):
    """Fetches top indexed songs for a given artist from LRCLIB."""
    print(f"\n🎤 Sweeping top tracks for artist: '{artist_name}'...")
    url = f"https://lrclib.net/api/search?q={requests.utils.quote(artist_name)}"
    discovered = []
    
    try:
        headers = {'User-Agent': 'MalachiDanielBot/2.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            tracks = resp.json()
            seen_titles = set()
            for t in tracks:
                t_name = t.get('trackName', '')
                a_name = t.get('artistName', '')
                clean_t = re.sub(r'\(.*?\)|\[.*?\]', '', t_name).strip()
                
                if clean_t and clean_t.lower() not in seen_titles:
                    seen_titles.add(clean_t.lower())
                    discovered.append({'title': clean_t, 'artist': a_name if a_name else artist_name})
            print(f"✅ Found {len(discovered)} tracks for '{artist_name}'.")
    except Exception as e:
        print(f"❌ Error sweeping artist '{artist_name}': {e}")
        
    return discovered

def process_and_fetch_song(title, artist, existing_slugs):
    """Checks if song exists; if missing, runs omni_fetcher waterfall logic."""
    target_slug = f"{slugify(title)}-{slugify(artist)}"
    
    # Check if we already have this file saved
    if target_slug in existing_slugs:
        print(f"⏭️ Skipping (Already Exists): '{title}' by '{artist}'")
        return False

    print(f"\n⚡ [NEW SONG DETECTED] Processing: '{title}' by '{artist}'...")
    
    # STEP 1: Direct LRCLIB Search
    lyrics, actual_title, actual_artist = fetch_from_lrclib(title, artist)
    
    corrected_title, corrected_artist = title, artist

    # STEP 2: AI Correction + LRCLIB Search
    if not lyrics:
        print("  ⚠️ Direct search failed. Running AI spell correction...")
        corrected_title, corrected_artist = fix_spelling_with_ai(title, artist)
        
        # Check slug again with corrected title
        corrected_slug = f"{slugify(corrected_title)}-{slugify(corrected_artist)}"
        if corrected_slug in existing_slugs:
            print(f"  ⏭️ Skipping (Corrected version already exists): '{corrected_title}'")
            return False

        if corrected_title != title or corrected_artist != artist:
            print(f"  ✨ Corrected Query: '{corrected_title}' by '{corrected_artist}'")
            lyrics, actual_title, actual_artist = fetch_from_lrclib(corrected_title, corrected_artist)

    # STEP 3: Web Scraper Fallback
    if not lyrics:
        print("  ⚠️ API returned no lyrics. Triggering Web Scraper...")
        scraped_lyrics = fetch_via_ddg_scraper(corrected_title, corrected_artist)
        if scraped_lyrics:
            lyrics = scraped_lyrics
            actual_title = corrected_title
            actual_artist = corrected_artist

    # SAVE RESULT
    if lyrics:
        save_title = actual_title if actual_title else title
        save_artist = actual_artist if actual_artist else artist
        save_lyrics(save_title, save_artist, lyrics)
        existing_slugs.add(f"{slugify(save_title)}-{slugify(save_artist)}")
        return True
    else:
        print(f"  ❌ Could not retrieve lyrics for '{title}'. Skipping.")
        return False

def main():
    print("========================================")
    print("  AUTOMATED DISCOVERY & OMNI-FETCHER    ")
    print("========================================")
    print("Choose Mode:")
    print("1. Scan iTunes Top 100 Christian Charts")
    print("2. Sweep Specific Worship Artists")
    print("3. Full Auto-Run (Charts + All Featured Artists)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    existing_slugs = get_existing_slugs()
    songs_to_process = []

    if choice == '1':
        songs_to_process.extend(discover_from_itunes_charts())
    elif choice == '2':
        print("\nFeatured Artists:", ", ".join(FEATURED_ARTISTS))
        custom_artist = input("Enter artist name (or press Enter to sweep featured list): ").strip()
        if custom_artist:
            songs_to_process.extend(discover_from_artist_sweep(custom_artist))
        else:
            for artist in FEATURED_ARTISTS:
                songs_to_process.extend(discover_from_artist_sweep(artist))
    elif choice == '3':
        songs_to_process.extend(discover_from_itunes_charts())
        for artist in FEATURED_ARTISTS:
            songs_to_process.extend(discover_from_artist_sweep(artist))
    else:
        print("Invalid choice.")
        return

    print(f"\n🔎 Total Discovered Candidates: {len(songs_to_process)}")
    print("Starting automated waterfall fetching process...\n")
    
    added_count = 0
    for song in songs_to_process:
        success = process_and_fetch_song(song['title'], song['artist'], existing_slugs)
        if success:
            added_count += 1
            # Brief pause to prevent rate limiting
            time.sleep(1)

    print("\n========================================")
    print(f"🎉 AUTO-DISCOVERY COMPLETE! Added {added_count} new songs.")
    print("========================================")
    print("Next Steps:")
    print("1. Run: python bulk_contextualizer.py")
    print("2. Run: python generator.py")

if __name__ == "__main__":
    main()