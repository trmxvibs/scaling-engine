# Instagram OSINT Tool
### By trmxvibs

---

![Banner](https://img.shields.io/badge/Instagram-OSINT-blueviolet?style=for-the-badge&logo=instagram)  
**Author:** trmxvibs

---

Instagram OSINT Tool is a simple Python-based utility for performing Open Source Intelligence (OSINT) tasks on public Instagram profiles.  
It allows you to:
- Analyze public Instagram profiles (bio, followers, posts, etc.)
- Download public post images and extract their metadata (EXIF, if available)
- Operate without requiring any Instagram API keys

> **For educational and ethical use only. Use responsibly and respect privacy.**

---

## Features
- Profile scraping (username, bio, follower stats, recent posts)
- Download and extract image metadata from public posts
- CLI-based, no API required

---

## Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/trmxvibs/scaling-engine.git
   cd scaling-engine
   ```

2. **Install required Python packages**
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Run the script from your terminal:

```bash
python insta_osint.py
```
You will be prompted to enter an Instagram username. For example:
```
Enter Instagram username: natgeo
```

The tool will output profile information and attempt to extract metadata from the latest public posts.

---

## Example Output

```
Profile:
Username: natgeo
Full Name: National Geographic
Bio: Experience the world through the eyes of National Geographic photographers.
Followers: 283000000
Following: 134
Posts: 32354
Verified: True
Private: False

External URL: https://www.nationalgeographic.com
Profile Pic: https://instagram.fxyz1-1.fna.fbcdn.net/...

Recent Posts and Metadata:
Post: https://instagram.fxyz1-1.fna.fbcdn.net/...
Caption: "Stunning sunset over the Amazon..."
Metadata: {'DateTimeOriginal': '2023:10:21 17:43:12', ...}
```

---

## Notes and Limitations

- Works only for public Instagram profiles.
- Most Instagram images have stripped metadata for privacy.
- Do not use for bulk scraping. Respect Instagram's robots.txt and rate limits.

---

## Ethical Notice

This tool is intended for educational use and legal, ethical OSINT research only.  
Do not use it to violate privacy or Instagram's terms of service.

---

## License

MIT License

---

**Happy investigating!**  
— trmxvibs
