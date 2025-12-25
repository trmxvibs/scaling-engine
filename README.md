<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=30&duration=3000&pause=1000&color=28C606&center=true&vCenter=true&width=600&lines=Insta+OSINT+Engine;Extract+Intel.+Analyze+Data.;Powered+By+trmxvibs;Scaling+Engine+v1.0" alt="Typing SVG" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/trmxvibs/scaling-engine?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/trmxvibs/scaling-engine?style=for-the-badge&logo=git&color=success" alt="Forks"/>
  <img src="https://img.shields.io/github/issues/trmxvibs/scaling-engine?style=for-the-badge&logo=github&color=green" alt="Issues"/>
  <img src="https://img.shields.io/github/license/trmxvibs/scaling-engine?style=for-the-badge&logo=open-source-initiative&color=2ea44f" alt="License"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python&color=32CD32" alt="Python"/>
  <img src="https://img.shields.io/badge/OSINT-Ready-orange?style=flat-square&logo=linux&color=228B22" alt="OSINT"/>
  <img src="https://img.shields.io/badge/Maintenance-Active-brightgreen?style=flat-square&color=00FF00" alt="Active"/>
  <img src="https://img.shields.io/badge/Built%20with-Passion-red?style=flat-square&color=32CD32" alt="Passion"/>
  <img src="https://img.shields.io/badge/Requests-%3E=_2.0-blue?style=flat-square" alt="Requests"/>
  <img src="https://img.shields.io/badge/BeautifulSoup-%3E=_4.0-yellow?style=flat-square" alt="BeautifulSoup"/>
  <img src="https://img.shields.io/badge/Pillow-%3E=_8.0-lightgrey?style=flat-square" alt="Pillow"/>
</p>

---

# Insta OSINT Engine — Extract Intel. Analyze Data.  
## Powered by trmxvibs — Scaling Engine v1.0

A lightweight, command-line Instagram OSINT utility that helps researchers, analysts, and security professionals extract public profile information, parse captions and bios for entities (emails, phone numbers, hashtags, mentions), optionally download media, and attempt EXIF / GPS extraction with reverse geocoding when available. Designed to be easy to run locally — no Instagram API key required for public profiles.

---

## Table of Contents

- Features
- Quick Start
- Installation
- Usage Examples
- CLI Options
- Output Format (sample)
- Notes & Limitations
- Legal & Ethics
- Troubleshooting
- Advanced Integrations & Next Steps
- Contributing
- Security
- License
- Contact

---

## ⚡ Features & Capabilities

<img src="https://img.shields.io/badge/Status-Operational-brightgreen?style=flat-square" alt="Status"/>

- Profile scraping: username, full name, bio, followers, following, post count, profile picture.
- Recent posts extraction (image/video URLs, shortcode, captions).
- Entity extraction from bio/captions: emails, phone numbers, URLs, hashtags, mentions.
- Optional media download (images saved locally).
- EXIF metadata extraction; GPS decoding → lat/lon conversion.
- Optional reverse-geocoding using Nominatim via geopy (human-readable place names).
- Polite networking: retries, timeouts, configurable delays.
- JSON output option for downstream processing and analysis.

---

## 🚀 Quick Start (1–2 minutes)

1. Clone the repository:
```bash
git clone https://github.com/trmxvibs/scaling-engine.git
cd scaling-engine
```

2. Create and activate a Python virtual environment (recommended):
```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

(Optional for reverse geocoding)
```bash
pip install geopy
```

---

## 🖥️ Usage Examples

Interactive (prompt):
```bash
python insta_osint.py
# Then enter username when asked, e.g. "natgeo"
```

Direct with username and options:
```bash
python insta_osint.py natgeo --download-images --images-dir data/images --exif-geolocate --json-out natgeo.json -v
```

Common examples:
- Basic:
  ```bash
  python insta_osint.py username
  ```
- Verbose:
  ```bash
  python insta_osint.py username -v
  ```
- Download images & save JSON:
  ```bash
  python insta_osint.py username --download-images --images-dir out/images --json-out out/username.json
  ```
- EXIF geolocation (requires geopy):
  ```bash
  python insta_osint.py username --exif-geolocate --json-out out/username.json
  ```

---

## 🔧 CLI Options

- username (positional) — Instagram username to analyze.
- -v, --verbose — enable verbose / debug logging.
- --download-images — download recent post images locally.
- --images-dir DIR — directory for downloaded images (default: insta_images).
- --exif-geolocate — extract EXIF and reverse-geocode GPS coordinates (requires geopy).
- --json-out FILE — write full JSON output to FILE.
- --max-posts N — number of recent posts to fetch (default 12, max 50).

---

## 📤 Output Format — Sample

The tool prints a readable summary and can save a detailed JSON file. Key fields:

- username, full_name, bio, followers, following, posts, profile_pic_url, external_url, is_verified, is_private
- bio_entities: emails, phones, urls, hashtags, mentions
- recent_posts: list of objects:
  - image_url, caption, shortcode, type
  - caption_entities
  - exif (raw EXIF if present)
  - gps: {lat, lon}
  - reverse_geocode: {address, raw}
  - downloaded_to (local path when downloaded)

Example (trimmed):
```json
{
  "username": "exampleuser",
  "full_name": "Example User",
  "bio": "Photographer | contact: me@example.com",
  "followers": 1234,
  "bio_entities": {
    "emails": ["me@example.com"],
    "phones": [],
    "urls": [],
    "hashtags": [],
    "mentions": []
  },
  "recent_posts": [
    {
      "image_url": "https://instagram.f.../xyz.jpg",
      "caption": "Sunset #nature",
      "shortcode": "ABC123",
      "caption_entities": {"hashtags": ["nature"], "mentions": []},
      "exif": {"Make": "Apple", "Model": "iPhone X", "GPSParsed": {...}, "GPSLatLon": {"lat": 12.34, "lon": 56.78}},
      "gps": {"lat": 12.34, "lon": 56.78},
      "reverse_geocode": {"address": "Some Place, City, Country"}
    }
  ]
}
```

> Note: Instagram often strips EXIF metadata — EXIF/GPS may frequently be absent.

---

## ⚠️ Notes & Limitations

- Works only for public profiles. Private profiles require authentication and may violate Terms of Service.
- Instagram frequently changes its page structure. The script has multiple fallbacks but scraping can break.
- Instagram rehosts and strips EXIF for many images; EXIF/GPS is rare.
- Reverse geocoding uses public Nominatim endpoints (geopy). Respect usage policy; do not bulk-query.
- For large-scale data collection use official APIs or provider agreements and ensure legal compliance.

---

## 🔒 Legal & Ethics

- Use this tool only for lawful, ethical, and authorized purposes: research, education, consenting clients, or permitted investigations.
- Do not attempt to access private content, brute-force accounts, or perform actions that violate platform Terms or local law.
- Always anonymize/pseudonymize sensitive results when sharing and follow data protection laws.

---

## 🛠 Troubleshooting

- "Failed to fetch profile" — Instagram may block or changed markup. Try again later or increase timeout.
- 429 / Rate limits — slow down requests, add longer delays, or run fewer concurrent queries.
- EXIF missing — original images typically retain metadata; Instagram-hosted copies usually don't.
- Reverse geocoding errors — ensure geopy is installed and you are not exceeding rate limits.

---

## 🔭 Advanced Integrations & Next Steps

Ideas you can enable for more power:
- Authenticated session support (cookie-based) to access follower lists or private content with permission.
- OCR (pytesseract) to extract embedded text from images.
- Face detection and clustering (face_recognition / OpenCV) for image similarity.
- Graph export & visualization (mentions/tag networks).
- Schedule periodic collections with Prefect / Airflow + monitoring and alerting.
- Store results in a database (Postgres / Elastic / BigQuery) and a simple frontend for searches.

---

## 🤝 Contributing

Contributions welcome. Suggested workflow:
1. Fork the repo.
2. Create a branch: `git checkout -b feat/your-feature`.
3. Add tests and update README/docs.
4. Open a PR with a clear description.

Please follow ethical guidelines — do not add features intended for abuse.

---

## 🛡 Security

- The tool makes external HTTP requests. Do not commit credentials. Use environment variables or secure stores for secrets.
- If you add login features, treat cookies and tokens as sensitive.
- Scanning or processing downloaded media may carry risk — treat unknown files carefully.

---

## 📜 License

Distributed under the MIT License. See LICENSE for details.

---

## 📬 Contact / Author

- Author: trmxvibs  
- Repo: https://github.com/trmxvibs/scaling-engine

---

If you want, I can:
- Commit this README to your repository and open a PR,
- Add additional shields (CI, coverage) if you set up GitHub Actions,
- Produce a short GitHub Actions workflow (CI) to run a smoke test,
- Create a bilingual README (English + Hindi),
- Or tailor the README tone/length for a specific audience.

Tell me which of these you'd like next and I'll prepare the files/PR.
