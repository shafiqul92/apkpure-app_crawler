# APKPure App Crawler 🕷️📱

A powerful, extensible Python-based crawler that downloads APK and XAPK files from [APKPure.com](https://apkpure.com), extracts rich metadata (title, version, size, permissions, SHA1, architecture, signature, etc.), and stores it in a structured MongoDB database. Ideal for research, reverse engineering, static analysis, app forensics, and large-scale Android dataset construction.

---

## 📌 Features

- Crawls apps from all major APKPure categories
- Downloads both `.apk` and `.xapk` formats
- Skips previously downloaded apps (no duplicates)
- Extracts rich metadata:
  - App title, package name, version
  - Architecture & required Android version
  - Signature, SHA1 hash, download count
  - File size, last update date
- Automatically creates MongoDB documents
-  Logs skipped or failed downloads to a text file

---


---

## ⚙️ Setup Instructions

###🔹 Step 1: Clone the Repository

```bash
git clone https://github.com/shafiqul92/apkpure-app_crawler.git
cd apkpure-app_crawler
```  

###🔹 Step 2: Create a Virtual Environment (Optional but Recommended)

```bash

python3 -m venv venv
source venv/bin/activate
```  
###🔹 Step 3: Install Python Dependencies
```bash

pip install -r requirements.txt

```  
###🔹 Step 4: Install the Project as a CLI Package

```bash

pip install .

```  
###🔹Step 5: Run Crawler

```bash
apkpure-crawl
```  





## 📁 Output Directory Structure

Downloaded APKs and XAPKs are saved here:


---

## 🧾 Example MongoDB Document

```json
{
  "title": "Home Planner",
  "version": "3.20.51",
  "package_name": "com.icandesignapp.all",
  "file_path": "apkpure_apks_final/house_and_home/Home Planner_3.20.51_APKPure.xapk",
  "added_at": "2025-07-26T17:56:28.382777",
  "metadata": {
    "Title": "Home Planner",
    "Version": "3.20.51",
    "Package Name": "com.icandesignapp.all",
    "Last updated": "Jul 25, 2025",
    "Requires Android": "Android 9.0+ (P, API 28)",
    "Architecture": "arm64-v8a",
    "Signature": "5814d271a7cabd1ea6ad3ef7db4d2a13a6c430fa",
    "APK Size": "1.1 GB",
    "Downloads": "300K+",
    "File SHA1": "1b9b49f4f45998daa3ea6bfcb6614f84b8e2c8e1"
  }
}

