#!/usr/bin/env python3

import os
import time
import re
import requests
from datetime import datetime
from pymongo import MongoClient
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
CATEGORIES = [
    "art_and_design", "auto_and_vehicles", "beauty", "books_and_reference",
    "business", "comics", "communication", "dating", "education", "entertainment",
    "events", "finance", "food_and_drink", "health_and_fitness", "house_and_home",
    "libraries_and_demo", "lifestyle", "maps_and_navigation", "medical",
    "music_and_audio", "news_and_magazines", "parenting", "personalization",
    "photography", "productivity", "shopping", "social", "sports", "tools",
    "travel_and_local", "video_players", "weather"
]
DESKTOP_BASE = "https://apkpure.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}
MAX_APPS = 10
DELAY = 1.0
SAVE_ROOT = "apkpure_apks_final_3"
SKIPPED_FILE = "skipped_apps.txt"

# ── MONGODB CONFIG ────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "apk_crawlerDB_final_3"
COLLECTION_NAME = "apks"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ── DB INSERT ─────────────────────────────────────────────────────────────────
def insert_into_db(title, version, package_name, file_path, metadata):
    document = {
        "title": title,
        "version": version,
        "package_name": package_name,
        "file_path": file_path,
        "metadata": metadata,
        "added_at": datetime.utcnow().isoformat()
    }
    result = collection.update_one(
        {"package_name": package_name, "version": version},
        {"$set": document},
        upsert=True
    )
    print(f"    ✔ {'Inserted' if result.upserted_id else 'Updated'} MongoDB: {package_name} {version}")

# ── LOG SKIPPED URLS ──────────────────────────────────────────────────────────
def log_skipped(title, version, reason=""):
    with open(SKIPPED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{title} {version} - {reason}\n")

# ── EXTRACT APP PAGE LINKS FROM CATEGORY ─────────────────────────────────────
def get_app_pages(category_url):
    print(f"[*] Fetching category: {category_url}")
    try:
        resp = requests.get(category_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch category: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    pages, seen = [], set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        path = urlparse(href).path.strip("/")
        parts = path.split("/", 1)
        if len(parts) == 2 and "." in parts[1] and not href.endswith("/download"):
            pkg = parts[1]
            if pkg not in seen:
                seen.add(pkg)
                pages.append(urljoin(DESKTOP_BASE, href))
                if len(pages) >= MAX_APPS:
                    break
    return pages

# ── PARSE METADATA AND FINAL DOWNLOAD LINK ───────────────────────────────────
def scrape_metadata_and_download_link(page_url):
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        log_skipped(page_url, "N/A", reason="Failed to fetch page")
        return "Unknown", "0.0.0", {}, None, None

    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("h1").text.strip() if soup.find("h1") else "Unknown"
    package_name = page_url.strip("/").split("/")[-1]

    version = "0.0.0"
    version_divs = soup.find_all(attrs={"data-dt-version": True})
    if version_divs:
        versions = [div["data-dt-version"] for div in version_divs]
        versions.sort(key=lambda v: v.count("."), reverse=True)
        version = versions[0]

    download_btn = soup.find("a", class_="da")
    if not download_btn or not download_btn.get("href"):
        log_skipped(title, version, reason="No download button")
        return title, version, {}, None, None

    intermediate_url = urljoin(page_url, download_btn["href"])

    try:
        resp2 = requests.get(intermediate_url, headers=HEADERS, timeout=10)
        resp2.raise_for_status()
        soup2 = BeautifulSoup(resp2.text, "html.parser")

        meta = {
            "Title": title,
            "Version": version,
            "Package Name": package_name
        }

        # Last updated
        updated = soup2.find(string=re.compile(r"(Last updated|Updated) on", re.I))
        if updated:
            date_match = re.search(r"(Last updated|Updated) on (.+)", updated, re.I)
            if date_match:
                meta["Last updated"] = date_match.group(2).strip()

        for info in soup2.find_all("div", class_="info"):
            label = info.find("div", class_="label one-line")
            value = info.find("div", class_="value double-lines")
            if label and value:
                key = label.get_text(strip=True)
                val = value.get_text(strip=True)
                if key not in ["Languages", "Content Rating"]:
                    meta[key] = val

        size_tag = soup2.find("span", string=re.compile(r"MB|GB", re.I))
        if size_tag:
            meta["APK Size"] = size_tag.text.strip()

        dl_tag = soup2.find("div", class_="head", string=re.compile(r"[\d,.]+[KMB]+", re.I))
        if dl_tag:
            meta["Downloads"] = dl_tag.text.strip()

        sig_div = soup2.find("div", class_="label", string=re.compile("Signature", re.I))
        if sig_div and sig_div.find_next_sibling("div", class_="value"):
            meta["Signature"] = sig_div.find_next_sibling("div", class_="value").text.strip()

        sha1_label = soup2.find("span", class_="label", string=re.compile("File SHA1", re.I))
        if sha1_label and sha1_label.find_next("span", class_="value"):
            meta["File SHA1"] = sha1_label.find_next("span", class_="value").text.strip()

        perms_link = soup2.find("a", href=True, string=re.compile("Permissions", re.I))
        if perms_link:
            perms_url = urljoin(intermediate_url, perms_link['href'])
            try:
                resp3 = requests.get(perms_url, headers=HEADERS, timeout=10)
                resp3.raise_for_status()
                soup3 = BeautifulSoup(resp3.text, "html.parser")
                perms = [li.text.strip() for li in soup3.select("ul.perms-list li") if li.text.strip()]
                if perms:
                    meta["Permissions"] = perms
            except:
                pass

        dl_link = soup2.find("a", id="download_link")
        if not dl_link or not dl_link.get("href"):
            log_skipped(title, version, reason="Missing final download link")
            return title, version, meta, None, None

        final_url = dl_link["href"]
        file_ext = ".xapk" if "xapk" in final_url.lower() else ".apk"
        return title, version, meta, final_url, file_ext

    except requests.RequestException:
        log_skipped(title, version, reason="Intermediate page failed")
        return title, version, {}, None, None

# ── DOWNLOAD APK/XAPK FILE ────────────────────────────────────────────────────
def download_file(final_url, title, version, save_dir, meta, file_ext):
    if not final_url:
        return

    safe_version = version.replace("/", "_")
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
    filename = f"{safe_title}_{safe_version}_APKPure{file_ext}"
    out_path = os.path.join(save_dir, filename)

    if os.path.exists(out_path):
        print(f"    ↪ Skipping (already exists): {filename}")
        return

    os.makedirs(save_dir, exist_ok=True)

    try:
        with requests.get(final_url, headers=HEADERS, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
    except requests.RequestException:
        log_skipped(title, version, reason="Download failed")
        return
    except FileNotFoundError:
        log_skipped(title, version, reason="Invalid file path")
        return

    insert_into_db(title, version, meta.get("Package Name", "Unknown"), out_path, meta)

# ── MAIN EXECUTION LOOP ───────────────────────────────────────────────────────
def main():
    for slug in CATEGORIES:
        category_url = f"{DESKTOP_BASE}/{slug}"
        save_dir = os.path.join(SAVE_ROOT, slug)
        os.makedirs(save_dir, exist_ok=True)

        pages = get_app_pages(category_url)
        for i, page in enumerate(pages, 1):
            print(f"\n→ ({i}/{len(pages)}) {page}")
            title, version, meta, final_url, file_ext = scrape_metadata_and_download_link(page)
            download_file(final_url, title, version, save_dir, meta, file_ext)
            time.sleep(DELAY)

    print("\n[✔] Crawling complete.")
    print(f"[!] Skipped entries logged in {SKIPPED_FILE}")

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

