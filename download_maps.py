#!/usr/bin/env python3
"""
Download Minnesota DNR snow depth maps from the weekly reports.

This script:
- Scrapes the MN DNR snow depth map index page
- Identifies all available weekly reports
- Downloads both depth maps and ranking maps (if available)
- Only downloads maps that aren't already in the data folder
- Uses date-based naming for easy organization
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

BASE_URL = "https://www.dnr.state.mn.us"
INDEX_URL = f"{BASE_URL}/climate/snowmap/index.html"
DATA_DIR = Path(__file__).parent / "data"


def fetch_page(url):
    """Fetch a web page with a proper user agent."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except (HTTPError, URLError) as e:
        print(f"Error fetching {url}: {e}")
        return None


def download_image(url, filepath):
    """Download an image file."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            data = response.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        return True
    except (HTTPError, URLError) as e:
        print(f"Error downloading {url}: {e}")
        return False


def crop_whitespace(filepath):
    """Remove white border from a JPG image."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return  # Skip cropping if Pillow isn't installed

    img = Image.open(filepath)
    # Create a diff against a pure-white background to find content bounds
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.convert("L").point(lambda x: 255 if x > 5 else 0).getbbox()
    if bbox:
        # Add a small margin
        margin = 20
        bbox = (
            max(0, bbox[0] - margin),
            max(0, bbox[1] - margin),
            min(img.width, bbox[2] + margin),
            min(img.height, bbox[3] + margin),
        )
        img.crop(bbox).save(filepath, quality=92)


def parse_date_from_link(link_text):
    """Parse date from link text like 'March 5, 2026'."""
    try:
        return datetime.strptime(link_text, "%B %d, %Y")
    except ValueError:
        return None


def extract_map_links(html):
    """Extract all snow depth map page links from the index page.

    Handles multiple URL formats used across the years:
      - /climate/snowmap/snow-depth-map-march-5-2026.html  (2020+)
      - snowmap_180322.html  (older, relative)
      - snowmap180322.html   (older, relative, no separator)
      - snowmap-181227.html  (older, relative, dash separator)
    """
    # Match any <a> with an href containing "snowmap" pointing to an .html page,
    # but exclude the index page, explanation page, etc.
    pattern = r'<a\s+href="([^"]*snowmap[^"]*\.html)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)

    INDEX_PAGE_URL = f"{BASE_URL}/climate/snowmap/index.html"

    map_links = []
    seen_dates = set()

    for href, link_text in matches:
        # Skip non-map pages
        if "explanation" in href or href.endswith("index.html"):
            continue

        date_obj = parse_date_from_link(link_text.strip())
        if not date_obj:
            continue

        date_str = date_obj.strftime("%Y-%m-%d")
        if date_str in seen_dates:
            continue
        seen_dates.add(date_str)

        # Resolve relative URLs against the index page directory
        if href.startswith("/"):
            full_url = urljoin(BASE_URL, href)
        elif href.startswith("http"):
            full_url = href
        else:
            full_url = f"{BASE_URL}/climate/snowmap/{href}"

        map_links.append({
            'url': full_url,
            'date': date_obj,
            'date_str': date_str,
        })

    return map_links


def extract_image_urls(html):
    """Extract snow depth map image URLs from a page."""
    images = []
    
    # Look for depth map - pattern like S260305.jpg or S260305.gif
    depth_pattern = r'https://images\.dnr\.state\.mn\.us/[^"]*/(S\d{6})\.(jpg|gif)'
    depth_matches = re.findall(depth_pattern, html)
    
    for filename, ext in depth_matches:
        if 'r' not in filename:  # Depth map doesn't have 'r' suffix
            url = f"https://images.dnr.state.mn.us/natural_resources/climate/current_conditions/snowmap/{filename}.{ext}"
            images.append({
                'url': url,
                'type': 'depth',
                'filename': f"{filename}.{ext}"
            })
        
        # Check for ranking map with 'r' suffix
        ranking_url = f"https://images.dnr.state.mn.us/natural_resources/climate/current_conditions/snowmap/{filename}r.{ext}"
        images.append({
            'url': ranking_url,
            'type': 'ranking',
            'filename': f"{filename}r.{ext}"
        })
    
    return images


def main():
    """Main function to download all missing maps."""
    DATA_DIR.mkdir(exist_ok=True)
    
    print("Fetching index page...")
    index_html = fetch_page(INDEX_URL)
    if not index_html:
        print("Failed to fetch index page")
        sys.exit(1)
    
    print("Extracting map links...")
    map_links = extract_map_links(index_html)
    print(f"Found {len(map_links)} map dates")
    
    downloaded_count = 0
    skipped_count = 0
    error_count = 0
    
    for map_info in sorted(map_links, key=lambda x: x['date'], reverse=True):
        date_str = map_info['date_str']
        print(f"\nProcessing {date_str}...")
        
        # Fetch the individual map page
        page_html = fetch_page(map_info['url'])
        if not page_html:
            error_count += 1
            continue
        
        # Extract image URLs
        images = extract_image_urls(page_html)
        
        for img in images:
            # Create filename: YYYY-MM-DD_depth.jpg or YYYY-MM-DD_ranking.jpg
            ext = img['filename'].split('.')[-1]
            local_filename = f"{date_str}_{img['type']}.{ext}"
            local_path = DATA_DIR / local_filename
            
            # Skip if already exists
            if local_path.exists():
                print(f"  ✓ Already exists: {local_filename}")
                skipped_count += 1
                continue
            
            # Download the image
            print(f"  ⬇ Downloading {img['type']} map...")
            if download_image(img['url'], local_path):
                if ext == 'jpg':
                    crop_whitespace(local_path)
                print(f"  ✓ Saved: {local_filename}")
                downloaded_count += 1
            else:
                # For ranking maps, it's okay if they don't exist (newer maps might not have them yet)
                if img['type'] == 'ranking':
                    print(f"  ℹ No ranking map available (expected for recent dates)")
                else:
                    print(f"  ✗ Failed to download: {local_filename}")
                    error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Downloaded: {downloaded_count}")
    print(f"  Skipped (already exists): {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"{'='*60}")

    generate_manifest()


def generate_manifest():
    """Generate data/manifest.js grouping depth maps by winter season.

    Season assignment uses the trailing year:
      Nov/Dec of year Y  →  season Y+1  (e.g. Nov 2025 → "2026")
      Jan–Oct of year Y  →  season Y    (e.g. Mar 2026 → "2026")
    """
    depth_files = sorted(DATA_DIR.glob("*_depth.*"))
    seasons = {}

    for f in depth_files:
        date_str = f.stem.replace("_depth", "")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        if date_obj.month >= 11:
            season = str(date_obj.year + 1)
        else:
            season = str(date_obj.year)

        seasons.setdefault(season, []).append({
            "date": date_str,
            "file": f.name,
        })

    # Sort each season chronologically
    for season in seasons:
        seasons[season].sort(key=lambda x: x["date"])

    manifest_path = DATA_DIR / "manifest.js"
    with open(manifest_path, "w") as fh:
        fh.write("const MANIFEST = ")
        json.dump(seasons, fh, indent=2, sort_keys=True)
        fh.write(";\n")

    total = sum(len(v) for v in seasons.values())
    print(f"\nGenerated manifest: {total} depth maps across {len(seasons)} seasons")


if __name__ == "__main__":
    if "--manifest-only" in sys.argv:
        generate_manifest()
    else:
        main()
