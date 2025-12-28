#!/usr/bin/env python3
"""
Corrected Insta OSINT script (insta_osnit.py)
Fixed: SyntaxError due to using MAX_POSTS before global declaration.
This file includes the enhanced functionality: scraping, entity extraction,
optional image download, EXIF parsing, and optional reverse geocoding.
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from PIL import ExifTags, Image
from urllib.parse import urljoin

# Optional dependency for reverse geocoding
try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except Exception:
    GEOPY_AVAILABLE = False

# HTTP retry & adapter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------- CONFIG ----------------------
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36 OSINTBot/1.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}
REQUEST_TIMEOUT = 15  # seconds
MAX_POSTS = 12  # default number of recent posts to extract (module-level constant)
DOWNLOAD_SLEEP = 0.5  # seconds between image downloads to be polite
# ----------------------------------------------------

logger = logging.getLogger("insta_osint")


def setup_session(retries: int = 3, backoff_factor: float = 0.3) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(DEFAULT_HEADERS)
    return s


def _recursive_find_user(obj):
    """
    Recursively search for a dict that looks like an Instagram 'user' object
    (has 'username' and 'profile_pic_url' or 'edge_owner_to_timeline_media').
    """
    if isinstance(obj, dict):
        if "username" in obj and ("profile_pic_url" in obj or "profile_pic_url_hd" in obj or "edge_owner_to_timeline_media" in obj):
            return obj
        for v in obj.values():
            res = _recursive_find_user(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = _recursive_find_user(item)
            if res:
                return res
    return None


def get_instagram_profile(session: requests.Session, username: str, polite_sleep: float = 0.3) -> Optional[Dict]:
    url = f"https://www.instagram.com/{username}/"
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        logger.error("Network error when fetching profile: %s", e)
        return None

    if resp.status_code == 404:
        logger.info("User '%s' not found (404).", username)
        return None
    if resp.status_code != 200:
        logger.error("Failed to fetch profile: HTTP %s", resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Try __NEXT_DATA__ (Next.js)
    shared = None
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            data = json.loads(script.string)
            user_info = _recursive_find_user(data)
            if user_info:
                shared = user_info
        except Exception:
            pass

    # 2) window._sharedData fallback (older)
    if not shared:
        scripts = soup.find_all("script", type="text/javascript")
        for s in scripts:
            if s.string and "window._sharedData" in s.string:
                try:
                    json_text = s.string.partition("=")[2].strip(" ;")
                    data = json.loads(json_text)
                    try:
                        user_info = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
                        shared = user_info
                        break
                    except Exception:
                        user_info = _recursive_find_user(data)
                        if user_info:
                            shared = user_info
                            break
                except Exception:
                    continue

    # 3) ld+json fallback
    if not shared:
        ld = soup.find("script", type="application/ld+json")
        if ld and ld.string:
            try:
                data = json.loads(ld.string)
                user_info = _recursive_find_user(data)
                if user_info:
                    shared = user_info
            except Exception:
                pass

    if not shared:
        logger.error("Failed to extract profile JSON. Instagram may have changed markup or scraping is blocked.")
        return None

    def safe_get(d, *keys, default=None):
        obj = d
        for k in keys:
            if not isinstance(obj, dict) or k not in obj:
                return default
            obj = obj[k]
        return obj

    user = shared
    profile = {
        "username": user.get("username"),
        "full_name": user.get("full_name") or user.get("fullName") or "",
        "bio": user.get("biography") or user.get("biography_text") or user.get("biog") or "",
        "followers": safe_get(user, "edge_followed_by", "count") or user.get("edge_followed_by_count") or user.get("followers") or 0,
        "following": safe_get(user, "edge_follow", "count") or user.get("edge_follow_count") or user.get("following") or 0,
        "posts": safe_get(user, "edge_owner_to_timeline_media", "count") or user.get("edge_owner_to_timeline_media_count") or user.get("media_count") or 0,
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or user.get("profilePicture"),
        "external_url": user.get("external_url") or user.get("externalWebsite") or "",
        "is_verified": user.get("is_verified") or False,
        "is_private": user.get("is_private") or False,
        "recent_posts": []
    }

    edges = safe_get(user, "edge_owner_to_timeline_media", "edges") or []
    if not edges:
        # try other common places
        edges = safe_get(user, "media", "nodes") or []

    for post in (edges[:MAX_POSTS] if isinstance(edges, list) else []):
        node = post.get("node", {}) if isinstance(post, dict) else {}
        img_url = node.get("display_url") or node.get("display_src") or node.get("thumbnail_src") or node.get("thumbnail_resources", [{}])[-1].get("src")
        caption_edges = node.get("edge_media_to_caption", {}).get("edges", []) if node else []
        caption = ""
        if caption_edges:
            try:
                caption = caption_edges[0].get("node", {}).get("text", "") or ""
            except Exception:
                caption = ""
        shortcode = node.get("shortcode") or node.get("code") or ""
        is_video = node.get("is_video", False)
        post_type = "video" if is_video else "image"
        profile["recent_posts"].append({
            "image_url": img_url,
            "caption": caption,
            "shortcode": shortcode,
            "type": post_type
        })
        time.sleep(polite_sleep)

    return profile


# ---------------- Extractors ----------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
HASHTAG_RE = re.compile(r"#(\w+)")
MENTION_RE = re.compile(r"@([A-Za-z0-9._]+)")

def extract_contacts_and_entities(text: str) -> Dict:
    if not text:
        return {"emails": [], "phones": [], "urls": [], "hashtags": [], "mentions": []}
    emails = sorted(set([m.group(0) for m in EMAIL_RE.finditer(text)]))
    phones = sorted(set([m.group(0) for m in PHONE_RE.finditer(text)]))
    urls = sorted(set([m.group(0) for m in URL_RE.finditer(text)]))
    hashtags = sorted(set(HASHTAG_RE.findall(text)))
    mentions = sorted(set(MENTION_RE.findall(text)))
    return {"emails": emails, "phones": phones, "urls": urls, "hashtags": hashtags, "mentions": mentions}


def extract_image_exif(session: requests.Session, image_url: str) -> Dict:
    if not image_url:
        return {}
    try:
        resp = session.get(image_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        exif_raw = getattr(img, "_getexif", lambda: None)()
        if not exif_raw:
            return {}
        exif = {}
        for tag_id, value in exif_raw.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            exif[str(tag)] = value
        # Try to decode GPS info nicely
        gps = exif.get("GPSInfo") or {}
        if gps:
            gps_parsed = {}
            for key in gps.keys():
                name = ExifTags.GPSTAGS.get(key, key)
                gps_parsed[name] = gps[key]
            exif["GPSParsed"] = gps_parsed
            try:
                latlon = _gps_parsed_to_latlon(gps_parsed)
                if latlon:
                    exif["GPSLatLon"] = {"lat": latlon[0], "lon": latlon[1]}
            except Exception:
                pass
        return exif
    except Exception as e:
        logger.warning("Error extracting EXIF from %s: %s", image_url, e)
        return {}


def _gps_parsed_to_latlon(gps_parsed: Dict) -> Optional[Tuple[float, float]]:
    """
    Convert GPSParsed (with keys 'GPSLatitude', 'GPSLatitudeRef', 'GPSLongitude', 'GPSLongitudeRef')
    to decimal lat/lon.
    """
    def _to_deg(value):
        # value is a tuple of tuples: ((deg_num,deg_den),(min_num,min_den),(sec_num,sec_den))
        try:
            d = value[0][0] / value[0][1]
            m = value[1][0] / value[1][1]
            s = value[2][0] / value[2][1]
            return d + (m / 60.0) + (s / 3600.0)
        except Exception:
            return None

    lat = None
    lon = None
    if "GPSLatitude" in gps_parsed and "GPSLatitudeRef" in gps_parsed:
        lat = _to_deg(gps_parsed["GPSLatitude"])
        if lat is None:
            return None
        if gps_parsed["GPSLatitudeRef"] in ("S", "south", "South"):
            lat = -lat
    if "GPSLongitude" in gps_parsed and "GPSLongitudeRef" in gps_parsed:
        lon = _to_deg(gps_parsed["GPSLongitude"])
        if lon is None:
            return None
        if gps_parsed["GPSLongitudeRef"] in ("W", "west", "West"):
            lon = -lon
    if lat is not None and lon is not None:
        return (lat, lon)
    return None


def reverse_geocode(lat: float, lon: float, user_agent: str = "insta_osint_bot", timeout: int = 10) -> Optional[Dict]:
    if not GEOPY_AVAILABLE:
        logger.debug("geopy not available; skipping reverse geocode")
        return None
    try:
        geolocator = Nominatim(user_agent=user_agent, timeout=timeout)
        loc = geolocator.reverse((lat, lon), language="en")
        if not loc:
            return None
        return {"address": loc.address, "raw": loc.raw}
    except Exception as e:
        logger.warning("Reverse geocode failed: %s", e)
        return None


# ---------------- Utilities ----------------
def safe_mkdir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.debug("Could not create dir %s: %s", path, e)


def download_image(session: requests.Session, url: str, dest_path: str) -> bool:
    if not url:
        return False
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return False


def analyze_instagram_user(session: requests.Session,
                           username: str,
                           download_images_flag: bool = False,
                           images_dir: str = "insta_images",
                           exif_geolocate: bool = False,
                           output_json: Optional[str] = None) -> Optional[Dict]:
    logger.info("Fetching profile for %s", username)
    profile = get_instagram_profile(session, username)
    if not profile:
        logger.error("Could not fetch profile for %s", username)
        return None

    # Entities from bio
    bio_entities = extract_contacts_and_entities(profile.get("bio", ""))
    profile["bio_entities"] = bio_entities

    # For each post extract caption entities and optional EXIF + geocode
    posts_out = []
    if download_images_flag:
        safe_mkdir(images_dir)

    for idx, post in enumerate(profile.get("recent_posts", []), start=1):
        caption = post.get("caption", "") or ""
        entities = extract_contacts_and_entities(caption)
        post_record = dict(post)
        post_record["caption_entities"] = entities

        image_url = post.get("image_url")
        if download_images_flag and image_url:
            fname = f"{username}_{post.get('shortcode') or idx}.jpg"
            dest = os.path.join(images_dir, fname)
            ok = download_image(session, image_url, dest)
            if ok:
                post_record["downloaded_to"] = dest
            else:
                post_record["downloaded_to"] = None
            time.sleep(DOWNLOAD_SLEEP)

        # EXIF extraction + GPS -> reverse geocode
        if exif_geolocate and image_url:
            exif = extract_image_exif(session, image_url)
            post_record["exif"] = exif
            gps = exif.get("GPSLatLon")
            if gps:
                lat = gps.get("lat")
                lon = gps.get("lon")
                post_record["gps"] = {"lat": lat, "lon": lon}
                rg = reverse_geocode(lat, lon)
                post_record["reverse_geocode"] = rg

        posts_out.append(post_record)

    profile["recent_posts"] = posts_out

    if output_json:
        try:
            with open(output_json, "w", encoding="utf-8") as fh:
                json.dump(profile, fh, ensure_ascii=False, indent=2)
            logger.info("Saved JSON output to %s", output_json)
        except Exception as e:
            logger.warning("Failed to save JSON output: %s", e)

    return profile


def pretty_print_profile(profile: Dict):
    if not profile:
        print("No profile data.")
        return
    print("--------- PROFILE ---------")
    print(f"Username: {profile.get('username')}")
    print(f"Full name: {profile.get('full_name')}")
    print(f"Bio: {profile.get('bio')}")
    print(f"Followers: {profile.get('followers')}  Following: {profile.get('following')}  Posts: {profile.get('posts')}")
    print(f"Profile pic: {profile.get('profile_pic_url')}")
    print(f"External: {profile.get('external_url')}")
    print("Bio entities:", profile.get("bio_entities", {}))
    print("\nRecent posts:")
    for p in profile.get("recent_posts", []):
        print("  - shortcode:", p.get("shortcode"))
        print("    type:", p.get("type"))
        print("    image:", p.get("image_url"))
        print("    caption:", (p.get("caption") or "")[:180])
        print("    caption_entities:", p.get("caption_entities"))
        if "downloaded_to" in p:
            print("    downloaded_to:", p.get("downloaded_to"))
        if "gps" in p:
            print("    gps:", p.get("gps"))
            if p.get("reverse_geocode"):
                print("    place:", p["reverse_geocode"].get("address"))
        print("")


def main():
    # Declare that we will modify the module-level MAX_POSTS variable if needed.
    global MAX_POSTS

    parser = argparse.ArgumentParser(description="Enhanced Instagram OSINT tool")
    parser.add_argument("username", nargs="?", help="Instagram username to analyze")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    parser.add_argument("--download-images", action="store_true", help="Download recent post images")
    parser.add_argument("--images-dir", default="insta_images", help="Directory to save downloaded images")
    parser.add_argument("--exif-geolocate", action="store_true", help="Extract EXIF and reverse-geocode GPS coordinates (requires geopy)")
    parser.add_argument("--json-out", help="Write full JSON output to this file")
    parser.add_argument("--max-posts", type=int, default=MAX_POSTS, help="Max number of recent posts to fetch")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Validate and clamp user-provided max posts, update module-level MAX_POSTS
    if args.max_posts:
        MAX_POSTS = max(1, min(50, args.max_posts))

    if args.exif_geolocate and not GEOPY_AVAILABLE:
        logger.warning("geopy not installed — reverse geocoding disabled. Install geopy to enable it.")

    session = setup_session()

    # Choose username: CLI arg or interactive prompt
    username = args.username
    if not username:
        try:
            username = input("Enter Instagram username: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)
        if not username:
            print("No username provided. Exiting.")
            sys.exit(0)

    profile = analyze_instagram_user(
        session=session,
        username=username,
        download_images_flag=args.download_images,
        images_dir=args.images_dir,
        exif_geolocate=args.exif_geolocate,
        output_json=args.json_out
    )

    if not profile:
        print("Analysis failed or user not available.")
        sys.exit(1)

    pretty_print_profile(profile)


if __name__ == "__main__":
    main()