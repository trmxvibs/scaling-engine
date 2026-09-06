import pytest
from io import BytesIO
from PIL import Image
from insta_osint import (
    parse_entities,
    _extract_lat_lon,
    compile_dossier,
    unshorten_url
)


def test_parse_entities_email_and_handles():
    sample_text = (
        "Contact me at support@recon.io or security@target.com. "
        "Follow @osint_lead and checkout #infosec #cybersecurity"
    )
    result = parse_entities(sample_text)
    
    assert "support@recon.io" in result["emails"]
    assert "security@target.com" in result["emails"]
    assert "osint_lead" in result["mentions"]
    assert "infosec" in result["hashtags"]


def test_parse_entities_phone_filtering():
    # Valid phone should be extracted, low-digit false positives ignored
    text = "Call office: +1 (555) 234-5678 or 12345 (random id)"
    result = parse_entities(text)
    
    assert any("555" in p for p in result["phones"])
    assert "12345" not in result["phones"]


def test_parse_entities_social_links():
    text = "Find my channels: https://t.me/mychannel and https://linktr.ee/myprofile"
    result = parse_entities(text)
    
    assert any("t.me/mychannel" in l for l in result["social_links"])
    assert any("linktr.ee/myprofile" in l for l in result["social_links"])


def test_gps_coordinate_math():
    # Mocking standard EXIF GPS tags for 40°26'46" N, 79°58'56" W
    mock_gps = {
        "GPSLatitude": ((40, 1), (26, 1), (46, 1)),
        "GPSLatitudeRef": "N",
        "GPSLongitude": ((79, 1), (58, 1), (56, 1)),
        "GPSLongitudeRef": "W"
    }
    lat, lon = _extract_lat_lon(mock_gps)
    
    assert round(lat, 2) == 40.45
    assert round(lon, 2) == -79.98


def test_compile_dossier_structure():
    mock_profile = {
        "username": "dummy_user",
        "full_name": "Dummy User",
        "followers": 100,
        "following": 50,
        "total_posts": 2,
        "is_private": False,
        "is_verified": False,
        "bio_intel": {
            "emails": ["dummy@test.com"],
            "phones": ["+1-800-555-0199"],
            "social_links": ["https://t.me/dummy"],
            "mentions": ["partner"]
        },
        "bio_ecosystem": [
            {
                "platform": "Linktree",
                "source_url": "https://linktr.ee/dummy",
                "resolved_url": "https://linktr.ee/dummy",
                "outbound_links": ["https://youtube.com/@dummy"],
                "discovered_entities": {"emails": [], "phones": [], "social_links": []}
            }
        ],
        "posts": []
    }
    
    dossier = compile_dossier(mock_profile)
    
    assert "dummy@test.com" in dossier["emails"]
    assert "+1-800-555-0199" in dossier["phones"]
    assert "@partner" in dossier["mentions"]
    assert any("youtube.com" in link for link in dossier["socials"])
