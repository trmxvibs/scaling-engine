#!/usr/bin/env python3
#Lokesh-kumar
# Date - 06/09/2026
"""
Insta OSINT Engine v2.0
Advanced Instagram Reconnaissance & Entity Aggregator
Features:
 - Dual-layer Profile Extraction (Web API fallback + HTML DOM Parsing)
 - Bio Link Ecosystem Resolver (Linktree, Beacons, Bento, Carrd)
 - Parallel Media Ingestion & EXIF GPS Geotagging
 - OCR Text & Handle Extraction via Tesseract
 - Unified Cross-Channel Terminal Dossier
 - Structured JSON and CSV Reporting Pipelines
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import ExifTags, Image

# Optional OCR integration
try:
    import pytesseract
    from PIL import ImageEnhance, ImageFilter
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# Optional Reverse Geocoding
try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

# ---------------- CONFIGURATION & CONSTANTS ----------------
APP_ID = "936619743392459"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.instagram.com",
    "Referer": "https://www.instagram.com/",
    "X-IG-App-ID": APP_ID,
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

REQUEST_TIMEOUT = 12

AGGREGATOR_DOMAINS = {
    "linktr.ee": "Linktree",
    "beacons.ai": "Beacons",
    "bento.me": "Bento",
    "carrd.co": "Carrd",
    "bio.link": "BioLink",
    "taplink.cc": "Taplink"
}

IGNORED_DOMAINS = {
    "instagram.com", "facebook.com", "meta.com", "policies.google.com",
    "cookieinformation.com", "trustarc.com"
}

logger = logging.getLogger("insta_osint")

# ---------------- REGEX & ENTITY DETECTORS ----------------
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b")
HASHTAG_REGEX = re.compile(r"#(\w+)")
MENTION_REGEX = re.compile(r"@([A-Za-z0-9._]+)")
SOCIAL_DOMAINS = [
    "t.me", "telegram.me", "wa.me", "twitter.com", "x.com",
    "linktr.ee", "youtube.com", "github.com", "linkedin.com", "tiktok.com"
]


def create_session(proxy: Optional[str] = None, cookies: Optional[str] = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    if cookies:
        session.headers.update({"Cookie": cookies})
    return session


def parse_entities(text: str) -> Dict[str, List[str]]:
    if not text:
        return {"emails": [], "phones": [], "social_links": [], "hashtags": [], "mentions": []}

    emails = sorted(set(EMAIL_REGEX.findall(text)))
    hashtags = sorted(set(HASHTAG_REGEX.findall(text)))
    mentions = sorted(set(MENTION_REGEX.findall(text)))

    raw_phones = PHONE_REGEX.findall(text)
    clean_phones = sorted(set(
        p.strip() for p in raw_phones
        if sum(c.isdigit() for c in p) >= 8 and not p.isdigit()
    ))

    social_links = []
    tokens = re.split(r"[\s,]+", text)
    for token in tokens:
        clean_token = token.strip("()[]<>{}\"'")
        if any(dom in clean_token.lower() for dom in SOCIAL_DOMAINS):
            social_links.append(clean_token)

    return {
        "emails": emails,
        "phones": clean_phones,
        "social_links": sorted(set(social_links)),
        "hashtags": hashtags,
        "mentions": mentions
    }


# ---------------- PROFILE FETCHERS ----------------
def fetch_profile_via_api(session: requests.Session, username: str) -> Optional[Dict]:
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("user")
        elif resp.status_code == 404:
            logger.warning("Target user '%s' does not exist (404).", username)
            return None
        logger.debug("API Endpoint returned status %s. Falling back to HTML extraction.", resp.status_code)
    except Exception as err:
        logger.debug("API fetch failed: %s", err)
    return None


def fetch_profile_via_html(session: requests.Session, username: str) -> Optional[Dict]:
    url = f"https://www.instagram.com/{username}/"
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Fallback 1: __NEXT_DATA__
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            data = json.loads(script.string)
            user = _find_user_dict(data)
            if user:
                return user

        # Fallback 2: ld+json
        for ld in soup.find_all("script", type="application/ld+json"):
            if ld.string:
                data = json.loads(ld.string)
                user = _find_user_dict(data)
                if user:
                    return user
    except Exception as err:
        logger.debug("HTML extraction failed: %s", err)
    return None


def _find_user_dict(obj: Any) -> Optional[Dict]:
    if isinstance(obj, dict):
        if "username" in obj and ("edge_owner_to_timeline_media" in obj or "profile_pic_url" in obj):
            return obj
        for val in obj.values():
            found = _find_user_dict(val)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_user_dict(item)
            if found:
                return found
    return None


# ---------------- BIO LINK RESOLVER ----------------
def unshorten_url(session: requests.Session, url: str, timeout: int = 8) -> str:
    try:
        resp = session.head(url, allow_redirects=True, timeout=timeout)
        return resp.url
    except Exception:
        try:
            resp = session.get(url, allow_redirects=True, timeout=timeout, stream=True)
            return resp.url
        except Exception:
            return url


def parse_aggregator_page(session: requests.Session, target_url: str) -> Dict[str, Any]:
    results = {
        "platform": "Direct / External",
        "resolved_url": target_url,
        "outbound_links": [],
        "discovered_entities": {"emails": [], "phones": [], "social_links": []}
    }

    parsed_target = urlparse(target_url)
    target_netloc = parsed_target.netloc.lower()

    for domain, name in AGGREGATOR_DOMAINS.items():
        if domain in target_netloc:
            results["platform"] = name
            break

    try:
        resp = session.get(target_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return results

        results["resolved_url"] = resp.url
        soup = BeautifulSoup(resp.text, "html.parser")

        page_text = soup.get_text(separator=" ", strip=True)
        results["discovered_entities"] = parse_entities(page_text)

        outbound = set()
        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            if not raw_href or raw_href.startswith(("#", "javascript:")):
                continue

            if raw_href.startswith("mailto:"):
                em = raw_href.replace("mailto:", "").split("?")[0].strip()
                if em and em not in results["discovered_entities"]["emails"]:
                    results["discovered_entities"]["emails"].append(em)
                continue

            if raw_href.startswith("tel:"):
                ph = raw_href.replace("tel:", "").split("?")[0].strip()
                if ph and ph not in results["discovered_entities"]["phones"]:
                    results["discovered_entities"]["phones"].append(ph)
                continue

            full_url = urljoin(resp.url, raw_href)
            parsed_href = urlparse(full_url)
            href_netloc = parsed_href.netloc.lower()

            if href_netloc in target_netloc or target_netloc in href_netloc:
                path = parsed_href.path.lower()
                if any(x in path for x in ["/login", "/signup", "/legal", "/privacy", "/terms", "/report"]):
                    continue

            if any(ign in href_netloc for ign in IGNORED_DOMAINS):
                continue

            if parsed_href.scheme in ("http", "https"):
                outbound.add(full_url)

        results["outbound_links"] = sorted(outbound)
        link_entities = parse_entities(" ".join(results["outbound_links"]))
        results["discovered_entities"]["social_links"] = sorted(
            set(results["discovered_entities"]["social_links"] + link_entities["social_links"])
        )
    except Exception as err:
        logger.debug("Failed to resolve aggregator links from %s: %s", target_url, err)

    return results


def resolve_all_bio_links(session: requests.Session, profile_data: Dict) -> List[Dict[str, Any]]:
    candidate_urls = set()
    ext_url = profile_data.get("external_url")
    if ext_url:
        candidate_urls.add(ext_url)

    for link in profile_data.get("bio_intel", {}).get("social_links", []):
        if link.startswith(("http://", "https://")):
            candidate_urls.add(link)
        else:
            candidate_urls.add(f"https://{link}")

    resolved_records = []
    for raw_url in candidate_urls:
        logger.info("Resolving bio redirect and destinations: %s", raw_url)
        canonical = unshorten_url(session, raw_url)
        page_analysis = parse_aggregator_page(session, canonical)
        page_analysis["source_url"] = raw_url
        resolved_records.append(page_analysis)

    return resolved_records


# ---------------- OCR & IMAGE ENHANCEMENT ----------------
def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    gray = img.convert("L")
    enhanced = ImageEnhance.Contrast(gray).enhance(1.8)
    return enhanced.filter(ImageFilter.SHARPEN)


def extract_ocr_from_image(image_input: Any) -> Dict[str, Any]:
    result = {
        "raw_text": "",
        "entities": {"emails": [], "phones": [], "social_links": [], "hashtags": [], "mentions": []},
        "success": False,
        "error": None
    }

    if not PYTESSERACT_AVAILABLE:
        result["error"] = "pytesseract library not available"
        return result

    try:
        if isinstance(image_input, (bytes, bytearray)):
            img = Image.open(BytesIO(image_input))
        elif isinstance(image_input, str) and os.path.exists(image_input):
            img = Image.open(image_input)
        else:
            result["error"] = "Invalid image input"
            return result

        processed = preprocess_image_for_ocr(img)
        raw_text = pytesseract.image_to_string(processed, config="--psm 11").strip()

        if raw_text:
            result["raw_text"] = raw_text
            result["entities"] = parse_entities(raw_text)
            result["success"] = True
    except Exception as err:
        result["error"] = str(err)
        logger.debug("OCR extraction error: %s", err)

    return result


# ---------------- EXIF & MEDIA INGESTION ----------------
def parse_exif(image_bytes: bytes) -> Dict[str, Any]:
    try:
        img = Image.open(BytesIO(image_bytes))
        raw_exif = getattr(img, "_getexif", lambda: None)()
        if not raw_exif:
            return {}

        exif = {}
        for tag_id, value in raw_exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            exif[tag_name] = value

        gps_info = exif.get("GPSInfo")
        if gps_info:
            gps_parsed = {ExifTags.GPSTAGS.get(k, str(k)): v for k, v in gps_info.items()}
            lat_lon = _extract_lat_lon(gps_parsed)
            if lat_lon:
                exif["GPSLatLon"] = {"latitude": lat_lon[0], "longitude": lat_lon[1]}
        return exif
    except Exception:
        return {}


def _extract_lat_lon(gps: Dict) -> Optional[Tuple[float, float]]:
    def to_decimal(coords):
        try:
            d = coords[0][0] / coords[0][1]
            m = coords[1][0] / coords[1][1]
            s = coords[2][0] / coords[2][1]
            return d + (m / 60.0) + (s / 3600.0)
        except Exception:
            return None

    lat = to_decimal(gps.get("GPSLatitude")) if "GPSLatitude" in gps else None
    lon = to_decimal(gps.get("GPSLongitude")) if "GPSLongitude" in gps else None
    if lat and gps.get("GPSLatitudeRef") in ("S", "South"):
        lat = -lat
    if lon and gps.get("GPSLongitudeRef") in ("W", "West"):
        lon = -lon
    return (lat, lon) if (lat is not None and lon is not None) else None


def download_post_asset(session: requests.Session, url: str, out_dir: str, filename: str, run_ocr: bool = False) -> Tuple[bool, Optional[str], Dict, Dict]:
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, filename)
            with open(path, "wb") as f:
                f.write(resp.content)

            exif = parse_exif(resp.content)
            ocr = extract_ocr_from_image(resp.content) if run_ocr else {}
            return True, path, exif, ocr
    except Exception as err:
        logger.debug("Asset download failed: %s: %s", url, err)
    return False, None, {}, {}


# ---------------- CONSOLE DOSSIER PRINTER ----------------
def compile_dossier(profile: Dict[str, Any]) -> Dict[str, Any]:
    dossier = {
        "emails": defaultdict(set),
        "phones": defaultdict(set),
        "socials": defaultdict(set),
        "mentions": defaultdict(set),
        "locations": [],
        "ocr_snippets": []
    }

    # Bio Sources
    bio_intel = profile.get("bio_intel", {})
    for email in bio_intel.get("emails", []):
        dossier["emails"][email].add("Bio")
    for phone in bio_intel.get("phones", []):
        dossier["phones"][phone].add("Bio")
    for link in bio_intel.get("social_links", []):
        dossier["socials"][link].add("Bio Outbound")
    for mention in bio_intel.get("mentions", []):
        dossier["mentions"][f"@{mention}"].add("Bio Mention")

    # Bio Ecosystem
    for ecosystem in profile.get("bio_ecosystem", []):
        platform_name = ecosystem.get("platform", "Direct")
        label = f"Aggregator ({platform_name})"
        ents = ecosystem.get("discovered_entities", {})
        for email in ents.get("emails", []):
            dossier["emails"][email].add(label)
        for phone in ents.get("phones", []):
            dossier["phones"][phone].add(label)
        for link in ents.get("social_links", []):
            dossier["socials"][link].add(label)
        for out in ecosystem.get("outbound_links", []):
            dossier["socials"][out].add(f"Resolved from {ecosystem.get('source_url')}")

    # Posts, Captions & OCR
    for post in profile.get("posts", []):
        post_label = f"Post [{post.get('shortcode')}]"
        c_ents = post.get("entities", {})
        for email in c_ents.get("emails", []):
            dossier["emails"][email].add(f"{post_label} Caption")
        for phone in c_ents.get("phones", []):
            dossier["phones"][phone].add(f"{post_label} Caption")
        for link in c_ents.get("social_links", []):
            dossier["socials"][link].add(f"{post_label} Caption")
        for mention in c_ents.get("mentions", []):
            dossier["mentions"][f"@{mention}"].add(f"{post_label} Caption")

        gps = post.get("exif", {}).get("GPSLatLon")
        if gps:
            dossier["locations"].append({
                "source": post_label,
                "lat": gps.get("latitude"),
                "lon": gps.get("longitude")
            })

        ocr = post.get("ocr", {})
        if ocr.get("success"):
            raw = ocr.get("raw_text", "").strip()
            if raw:
                dossier["ocr_snippets"].append({
                    "source": post_label,
                    "text": " ".join(raw.split()[:14]) + "..."
                })
            for email in ocr.get("entities", {}).get("emails", []):
                dossier["emails"][email].add(f"{post_label} OCR")
            for phone in ocr.get("entities", {}).get("phones", []):
                dossier["phones"][phone].add(f"{post_label} OCR")
            for mention in ocr.get("entities", {}).get("mentions", []):
                dossier["mentions"][f"@{mention}"].add(f"{post_label} OCR")

    return dossier


def print_terminal_dossier(profile: Dict[str, Any]):
    dossier = compile_dossier(profile)
    w = 72

    c_cyan = "\033[96m"
    c_green = "\033[92m"
    c_yellow = "\033[93m"
    c_white = "\033[97m"
    c_gray = "\033[90m"
    c_bold = "\033[1m"
    c_reset = "\033[0m"

    print(f"\n{c_cyan}╔═{'═' * (w - 4)}═╗{c_reset}")
    title = f" TARGET DOSSIER: @{profile.get('username')} "
    print(f"{c_cyan}║{c_bold}{c_white}{title.center(w - 2)}{c_reset}{c_cyan}║{c_reset}")
    print(f"{c_cyan}╠═{'═' * (w - 4)}═╣{c_reset}")

    meta1 = f" Name: {profile.get('full_name') or 'N/A'}  |  ID: {profile.get('id') or 'N/A'}"
    meta2 = f" Followers: {profile.get('followers'):,}  |  Following: {profile.get('following'):,}  |  Posts: {profile.get('total_posts'):,}"
    meta3 = f" Account: {'[PRIVATE]' if profile.get('is_private') else '[PUBLIC]'}  |  Status: {'[VERIFIED]' if profile.get('is_verified') else '[STANDARD]'}"

    for m in (meta1, meta2, meta3):
        print(f"{c_cyan}║{c_reset} {m.ljust(w - 4)} {c_cyan}║{c_reset}")

    def section(title_text):
        bar = f"── {title_text} "
        print(f"{c_cyan}╟{c_yellow}{c_bold}{bar.ljust(w - 2, '─')}{c_reset}{c_cyan}╢{c_reset}")

    # Contact Vectors
    section("IDENTIFIED CONTACT VECTORS")
    has_contacts = False
    if dossier["emails"]:
        has_contacts = True
        for email, sources in dossier["emails"].items():
            s_str = f"({', '.join(sorted(sources))})"
            print(f"{c_cyan}║{c_reset}  {c_green}● Email   :{c_reset} {email.ljust(26)} {c_gray}{s_str}{c_reset}")
    if dossier["phones"]:
        has_contacts = True
        for phone, sources in dossier["phones"].items():
            s_str = f"({', '.join(sorted(sources))})"
            print(f"{c_cyan}║{c_reset}  {c_green}● Phone   :{c_reset} {phone.ljust(26)} {c_gray}{s_str}{c_reset}")
    if not has_contacts:
        print(f"{c_cyan}║{c_reset}  {c_gray}[No explicit contact vectors found]{c_reset}")

    # External Footprint
    section("RESOLVED EXTERNAL & BIO LINKS")
    if dossier["socials"]:
        for link, sources in dossier["socials"].items():
            s_str = f"({', '.join(sorted(sources))})"
            print(f"{c_cyan}║{c_reset}  {c_cyan}➜{c_reset} {link[:44].ljust(45)} {c_gray}{s_str}{c_reset}")
    else:
        print(f"{c_cyan}║{c_reset}  {c_gray}[No external links resolved]{c_reset}")

    # Mentioned Accounts
    section("ASSOCIATED HANDLES & MENTIONS")
    if dossier["mentions"]:
        mention_items = list(dossier["mentions"].items())[:10]
        for handle, sources in mention_items:
            s_str = f"({', '.join(sorted(sources))})"
            print(f"{c_cyan}║{c_reset}  {c_white}{handle.ljust(22)}{c_reset} {c_gray}{s_str}{c_reset}")
        if len(dossier["mentions"]) > 10:
            print(f"{c_cyan}║{c_reset}  {c_gray}... and {len(dossier['mentions']) - 10} more accounts.{c_reset}")
    else:
        print(f"{c_cyan}║{c_reset}  {c_gray}[No account mentions extracted]{c_reset}")

    # OCR Extracts
    if dossier["ocr_snippets"]:
        section("OPTICAL CHARACTER RECOGNITION (OCR)")
        for snip in dossier["ocr_snippets"][:4]:
            print(f"{c_cyan}║{c_reset}  {c_yellow}[{snip['source']}]{c_reset} {c_white}\"{snip['text']}\"{c_reset}")

    # Geolocation
    if dossier["locations"]:
        section("GEOLOCATION METADATA")
        for loc in dossier["locations"]:
            print(f"{c_cyan}║{c_reset}  {c_green}📍 {loc['source']}:{c_reset} Lat {loc['lat']}, Lon {loc['lon']}")

    print(f"{c_cyan}╚═{'═' * (w - 4)}═╝{c_reset}\n")


# ---------------- EXPORT CONTROLLERS ----------------
def export_csv(record: Dict[str, Any], filepath: str):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Shortcode", "Post URL", "Type", "Caption Entities", "OCR Emails", "OCR Phones", "Local File"])
        for p in record.get("posts", []):
            ocr = p.get("ocr", {}).get("entities", {})
            writer.writerow([
                p.get("shortcode"),
                p.get("url"),
                p.get("type"),
                "; ".join(p.get("entities", {}).get("emails", [])),
                "; ".join(ocr.get("emails", [])),
                "; ".join(ocr.get("phones", [])),
                p.get("local_path") or ""
            ])
    logger.info("CSV report saved: %s", filepath)


# ---------------- PIPELINE RUNNER ----------------
def run_audit(username: str, max_posts: int = 12, download: bool = False,
              out_dir: str = "insta_recon", proxy: Optional[str] = None,
              cookies: Optional[str] = None, run_ocr: bool = False) -> Optional[Dict[str, Any]]:

    session = create_session(proxy=proxy, cookies=cookies)
    logger.info("Initiating intelligence scan for target: @%s", username)

    user_data = fetch_profile_via_api(session, username) or fetch_profile_via_html(session, username)
    if not user_data:
        logger.error("Could not fetch target. Profile may be private, rate-limited, or blocked.")
        return None

    bio_text = user_data.get("biography") or ""
    profile_record = {
        "id": user_data.get("id"),
        "username": user_data.get("username"),
        "full_name": user_data.get("full_name"),
        "is_private": user_data.get("is_private", False),
        "is_verified": user_data.get("is_verified", False),
        "external_url": user_data.get("external_url"),
        "followers": user_data.get("edge_followed_by", {}).get("count", 0),
        "following": user_data.get("edge_follow", {}).get("count", 0),
        "total_posts": user_data.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "bio": bio_text,
        "bio_intel": parse_entities(bio_text + f" {user_data.get('external_url') or ''}"),
        "profile_pic": user_data.get("profile_pic_url_hd") or user_data.get("profile_pic_url"),
        "posts": [],
        "bio_ecosystem": []
    }

    # Deep Bio & Aggregator Link Resolution
    profile_record["bio_ecosystem"] = resolve_all_bio_links(session, profile_record)

    # Post processing setup
    edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])[:max_posts]
    posts_to_process = []

    for edge in edges:
        node = edge.get("node", {})
        c_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = c_edges[0].get("node", {}).get("text", "") if c_edges else ""

        post_obj = {
            "id": node.get("id"),
            "shortcode": node.get("shortcode"),
            "url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
            "type": "Video" if node.get("is_video") else "Image",
            "caption": caption,
            "entities": parse_entities(caption),
            "media_url": node.get("display_url"),
            "local_path": None,
            "exif": {},
            "ocr": {}
        }
        posts_to_process.append(post_obj)

    # Concurrent Asset Ingestion & Analysis
    if download and posts_to_process:
        user_media_dir = os.path.join(out_dir, username)
        logger.info("Executing concurrent downloads and OCR across thread pool...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    download_post_asset,
                    session,
                    post["media_url"],
                    user_media_dir,
                    f"{post['shortcode']}.jpg",
                    run_ocr
                ): post for post in posts_to_process if post["media_url"]
            }
            for fut in as_completed(futures):
                post_ref = futures[fut]
                ok, path, exif, ocr_data = fut.result()
                if ok:
                    post_ref["local_path"] = path
                    post_ref["exif"] = exif
                    post_ref["ocr"] = ocr_data

    profile_record["posts"] = posts_to_process
    return profile_record


# ---------------- CLI ENTRYPOINT ----------------
def main():
    parser = argparse.ArgumentParser(
        description="Insta OSINT Engine v2.0 - High Throughput Intel & Entity Aggregator"
    )
    parser.add_argument("username", nargs="?", help="Target Instagram handle")
    parser.add_argument("--max-posts", type=int, default=12, help="Number of recent posts to crawl (Default: 12)")
    parser.add_argument("--download", action="store_true", help="Download media files concurrently")
    parser.add_argument("--ocr", action="store_true", help="Extract text and contacts from post media using Tesseract")
    parser.add_argument("--out-dir", default="insta_recon", help="Directory for output files")
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--cookies", help="Raw Cookie header string to bypass rate limits")
    parser.add_argument("--json", action="store_true", help="Export full profile tree to JSON")
    parser.add_argument("--csv", action="store_true", help="Export posts and entities to CSV")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s"
    )

    username = args.username
    if not username:
        try:
            username = input("Enter target Instagram handle: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    if not username:
        print("Error: Target handle is required.")
        sys.exit(1)

    result = run_audit(
        username=username,
        max_posts=args.max_posts,
        download=args.download,
        out_dir=args.out_dir,
        proxy=args.proxy,
        cookies=args.cookies,
        run_ocr=args.ocr
    )

    if not result:
        sys.exit(1)

    print_terminal_dossier(result)

    os.makedirs(args.out_dir, exist_ok=True)
    if args.json:
        json_path = os.path.join(args.out_dir, f"{username}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info("JSON profile dossier written to %s", json_path)

    if args.csv:
        csv_path = os.path.join(args.out_dir, f"{username}_posts.csv")
        export_csv(result, csv_path)


if __name__ == "__main__":
    main()
