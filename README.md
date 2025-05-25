<!-- README.md for Instagram OSINT Tool -->

<p align="center">
  <img src="https://img.shields.io/badge/Instagram-OSINT-purple?style=for-the-badge&logo=instagram" alt="Instagram OSINT">
</p>

<h1 align="center">
  <img src="https://raw.githubusercontent.com/trmxvibs/scaling-engine/main/assets/insta_osint_banner.gif" width="80%"/><br>
  <span style="color:#9b59b6;">Instagram OSINT Tool</span>
</h1>
<h3 align="center" style="color:#e84393;">By <span style="color:#f1c40f;">trmxvibs</span></h3>

---

> <p align="center" style="color:#00b894;">A free, fast, and simple OSINT tool to analyze Instagram public profiles and extract image metadata – no API required!</p>

---

## 🌈 Features

- 🔎 **Instagram Profile Analysis** (bio, followers, posts, etc.)
- 🖼️ **Image Metadata Extraction** (EXIF, if available)
- ⚡ **No Instagram API Needed**
- 💻 **Works on Termux, Kali Linux, Parrot OS, WSL, Ubuntu, Windows, macOS & more**
- 🛡️ **For educational, ethical, and legal OSINT only!**

---

## 🚀 Installation

### 1. Clone this repository
```bash
git clone https://github.com/trmxvibs/scaling-engine.git
cd scaling-engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🖥️ Usage

Run the tool from your terminal:

```bash
python insta_osint.py
```
You will see a stylized banner, then be prompted to enter an Instagram username.

**Example:**
```
Enter Instagram username: natgeo
```

---

## 💡 Platform-Specific Quick Start

| Platform      | Command to Run Tool                               |
|---------------|---------------------------------------------------|
| **Termux**    | `python insta_osint.py`                           |
| **Kali Linux**| `python3 insta_osint.py`                          |
| **Parrot OS** | `python3 insta_osint.py`                          |
| **WSL**       | `python3 insta_osint.py`                          |
| **Ubuntu**    | `python3 insta_osint.py`                          |
| **Windows**   | `python insta_osint.py` (in CMD or PowerShell)    |
| **macOS**     | `python3 insta_osint.py`                          |

> _Tip: If `python` doesn't work, try `python3` instead._



## 🎨 Output Example

```ansi
\033[95mProfile:\033[0m
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

\033[94mRecent Posts and Metadata:\033[0m
Post: https://instagram.fxyz1-1.fna.fbcdn.net/...
Caption: "Stunning sunset over the Amazon..."
Metadata: {'DateTimeOriginal': '2023:10:21 17:43:12', ...}
```

---

## ⚠️ Notes & Limitations

- Only works for **public profiles**.
- Most Instagram images have very limited EXIF metadata.
- Use responsibly! Do not abuse or violate Instagram’s Terms of Service.

---

## 🌐 License & Legal

- **MIT License**
- For **educational and ethical OSINT** purposes only.  
- Always respect privacy and legal boundaries.

---

## 💛 Enjoy hacking with ethics!
<p align="center">
  <b>Instagram OSINT Tool • by trmxvibs</b><br>
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=F1C40F&center=true&vCenter=true&width=435&lines=Stay+curious+%F0%9F%92%AD;Happy+Hacking+%F0%9F%91%BB" alt="Typing SVG" />
</p>
