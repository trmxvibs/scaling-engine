import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

# ---------------------- BANNER ----------------------
BANNER = r"""
  _____           _                                      
 |_   _|         | |             ___  ____  _           
   | |  _ __  ___| |_    ___ ___|_ _|/ ___|| |_ ___ _ __ 
   | | | '_ \/ __| __|  / __/ _ \| |\___ \| __/ _ \ '__|
  _| |_| | | \__ \ |_  | (_|  __/| | ___) | ||  __/ |   
 |_____|_| |_|___/\__|  \___\___|___|____/ \__\___|_|   
 
             Instagram OSINT Tool
                  by trmxvibs
---------------------------------------------------------
"""
# -------------------------------------------------------

def get_instagram_profile(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; OSINTBot/1.0)",
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch profile: {resp.status_code}")
        return None
    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract shared data from script tag
    scripts = soup.find_all("script", type="text/javascript")
    shared_data = None
    for script in scripts:
        if script.string and "window._sharedData" in script.string:
            json_text = script.string.partition("=")[2].strip(" ;")
            shared_data = json.loads(json_text)
            break

    if not shared_data:
        print("Failed to extract profile data.")
        return None

    user_info = shared_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
    profile_data = {
        "username": user_info["username"],
        "full_name": user_info["full_name"],
        "bio": user_info["biography"],
        "followers": user_info["edge_followed_by"]["count"],
        "following": user_info["edge_follow"]["count"],
        "posts": user_info["edge_owner_to_timeline_media"]["count"],
        "profile_pic_url": user_info["profile_pic_url_hd"],
        "external_url": user_info["external_url"],
        "is_verified": user_info["is_verified"],
        "is_private": user_info["is_private"],
        "recent_posts": []
    }

    # Get recent post images
    posts = user_info["edge_owner_to_timeline_media"]["edges"]
    for post in posts:
        node = post["node"]
        img_url = node["display_url"]
        caption = node["edge_media_to_caption"]["edges"][0]["node"]["text"] if node["edge_media_to_caption"]["edges"] else ""
        profile_data["recent_posts"].append({
            "image_url": img_url,
            "caption": caption,
            "shortcode": node["shortcode"],
        })
    return profile_data

def extract_image_metadata(image_url):
    try:
        resp = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"})
        img = Image.open(BytesIO(resp.content))
        exif_data = img._getexif()
        if not exif_data:
            return {}
        metadata = {}
        for tag, value in exif_data.items():
            tag_name = Image.ExifTags.TAGS.get(tag, tag)
            metadata[tag_name] = value
        return metadata
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {}

def analyze_instagram_user(username):
    profile = get_instagram_profile(username)
    if not profile:
        print("Could not analyze user.")
        return
    print(f"Profile:\nUsername: {profile['username']}\nFull Name: {profile['full_name']}\nBio: {profile['bio']}\nFollowers: {profile['followers']}\nFollowing: {profile['following']}\nPosts: {profile['posts']}\nVerified: {profile['is_verified']}\nPrivate: {profile['is_private']}\n")
    print(f"External URL: {profile['external_url']}\nProfile Pic: {profile['profile_pic_url']}")
    print("\nRecent Posts and Metadata:")
    for post in profile["recent_posts"]:
        print(f"Post: {post['image_url']}\nCaption: {post['caption']}")
        meta = extract_image_metadata(post["image_url"])
        print(f"Metadata: {meta}\n")

if __name__ == "__main__":
    print(BANNER)
    username = input("Enter Instagram username: ")
    analyze_instagram_user(username)
