<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=30&duration=3000&pause=1000&color=28C606&center=true&vCenter=true&width=600&lines=Insta+OSINT+Engine+v2.0;Deep+Recon.+Aggregator+Resolver.;Parallel+Ingestion+%26+OCR;GPL-3.0+Open+Source" alt="Insta OSINT Engine"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&color=32CD32" alt="Python"/>
  <img src="https://img.shields.io/badge/OSINT-Framework-orange?style=for-the-badge&logo=linux&color=228B22" alt="OSINT"/>
  <img src="https://img.shields.io/badge/OCR-Tesseract-yellow?style=for-the-badge&logo=google&color=E65100" alt="OCR"/>
  <img src="https://img.shields.io/badge/License-GPLv3-blue?style=for-the-badge&color=2ea44f" alt="GPL-3.0"/>
</p>

---

# Insta OSINT Engine

### Reconnaissance & Entity Aggregation — v2.0

A command-line OSINT tool for analyzing **public Instagram profile data**, resolving public bio links, processing media, extracting visible text with OCR, parsing available EXIF metadata, and exporting structured intelligence.

> **For authorized research and publicly accessible information only.**

---

## Features

* **Profile Discovery** — Collects available public profile and post data.
* **Fallback Parsing** — Supports common public JSON/DOM structures such as `__NEXT_DATA__` and `ld+json`.
* **Bio Link Resolver** — Resolves public links from Linktree, Beacons, Bento, Carrd, Bio.link, and Taplink.
* **Concurrent Media Processing** — Downloads and processes media using a configurable worker pool.
* **OCR Extraction** — Uses Tesseract to extract visible text, emails, phone numbers, and account mentions from images.
* **EXIF Parsing** — Reads available image metadata, including GPS coordinates when present.
* **Entity Aggregation** — Combines discovered URLs, handles, contacts, captions, OCR results, and metadata.
* **JSON & CSV Export** — Generates structured investigation reports.
* **Proxy Support** — Supports HTTP and SOCKS5 proxies where required for legitimate network testing.

---

# Requirements

* Python **3.8+**
* Internet connection
* Tesseract OCR *(only required for `--ocr`)*
* Windows, Linux, macOS, or WSL

---

# Installation

## Linux / macOS / WSL

```bash
git clone https://github.com/trmxvibs/scaling-engine.git
cd scaling-engine

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Windows

### Command Prompt

```bat
git clone https://github.com/trmxvibs/scaling-engine.git
cd scaling-engine

setup.bat
```

### PowerShell

```powershell
git clone https://github.com/trmxvibs/scaling-engine.git
cd scaling-engine

.\setup.ps1
```

The setup scripts create the required environment and install dependencies.

---

# Tesseract OCR

Tesseract is required only when using the `--ocr` option.

### Ubuntu / Debian / WSL

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng
```

### macOS

```bash
brew install tesseract
```

### Windows

Install Tesseract and ensure its installation directory is available in the system `PATH`.

---

# Usage

## Linux / macOS / WSL

### Interactive Mode

```bash
python insta_osint.py
```

### Profile Scan

```bash
python insta_osint.py target_user --max-posts 25
```

### Full Scan

```bash
python insta_osint.py target_user --download --ocr --json --csv --out-dir recon_data
```

### Proxy

```bash
python insta_osint.py target_user --proxy "http://127.0.0.1:8080"
```

---

# Windows

## Option A — Command Prompt

### Setup

Run once:

```bat
setup.bat
```

### Start the tool

```bat
run.bat
```

### With arguments

```bat
run.bat target_user --download --ocr
```

Example with JSON export:

```bat
run.bat target_user --download --ocr --json
```

---

## Option B — PowerShell

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Setup

```powershell
.\setup.ps1
```

### Start the tool

```powershell
.\run.ps1
```

### With arguments

```powershell
.\run.ps1 target_user --download --ocr --json
```

---

# Command-Line Options

| Argument        | Type      | Default       | Description                             |
| --------------- | --------- | ------------- | --------------------------------------- |
| `username`      | String    | —             | Target public username.                 |
| `--max-posts`   | Integer   | `12`          | Number of recent posts to inspect.      |
| `--download`    | Flag      | Off           | Download available public media.        |
| `--ocr`         | Flag      | Off           | Run Tesseract OCR on downloaded images. |
| `--out-dir`     | Directory | `insta_recon` | Output directory.                       |
| `--json`        | Flag      | Off           | Generate JSON report.                   |
| `--csv`         | Flag      | Off           | Generate CSV report.                    |
| `--proxy`       | URL       | —             | HTTP or SOCKS5 proxy.                   |
| `--cookies`     | String    | —             | Custom cookies for authorized requests. |
| `-v, --verbose` | Flag      | Off           | Enable debug logging.                   |

---

# Output

A full run may produce:

```text
insta_recon/
├── <username>.json
├── <username>_posts.csv
└── <username>/
    ├── image_001.jpg
    ├── image_002.jpg
    └── ...
```

### JSON

Contains the collected profile, links, entities, metadata, and extraction results.

### CSV

Contains structured post-level information for further analysis.

### Media

Downloaded public media is stored under the target's directory.

---

# Processing Pipeline

```text
Public Profile
      │
      ├── Bio & Links
      ├── Posts & Captions
      └── Media
            │
            ├── OCR
            └── EXIF
                  │
                  ▼
           Entity Extraction
                  │
                  ▼
          Unified OSINT Data
             ┌────┴────┐
             ▼         ▼
            JSON      CSV
```

---

# Supported Link Aggregators

The resolver supports commonly used public link aggregation services, including:

* Linktree
* Beacons
* Bento
* Carrd
* Bio.link
* Taplink

Results depend on the information publicly exposed by each service.

---

# Security & Privacy

Use the tool only for:

* Authorized security research
* Digital forensics
* OSINT investigations
* Security auditing
* Analysis of publicly accessible information

Do not use it to access private accounts, bypass authentication, evade access controls, or collect information without a legitimate basis.

---

# Legal Disclaimer

This project is provided for educational and legitimate security-research purposes.

Users are responsible for complying with applicable laws, privacy regulations, and platform policies. The authors and contributors are not responsible for misuse of the software or information obtained through it.

---

# License

Licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

See the `LICENSE` file for the complete license terms.

---

<p align="center">

**Insta OSINT Engine v2.0**

`Recon` • `Aggregation` • `OCR` • `EXIF` • `JSON` • `CSV`

</p>
