import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "Datasets"
RAW_PATH = DATASETS_DIR / "amazon_laptops.csv"
SEARCH_URL = "https://www.amazon.in/s"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def clean_price_text(value: str) -> str:
    if not value:
        return "N/A"
    return re.sub(r"[^0-9]", "", value) or "N/A"


def extract_product_title(block) -> str:
    title = None
    selectors = [
        lambda b: b.find("span", class_=lambda x: x and "a-text-normal" in x),
        lambda b: b.find("h2"),
        lambda b: b.select_one("span.a-size-medium.a-color-base.a-text-normal"),
    ]
    for selector in selectors:
        title = selector(block)
        if title:
            candidate = title.get_text(" ", strip=True)
            if candidate and len(candidate) >= 10:
                return candidate

    anchor_texts = [
        a.get_text(" ", strip=True)
        for a in block.find_all("a", href=True)
        if a.get_text(" ", strip=True)
    ]
    for candidate in anchor_texts:
        cleaned = re.sub(r"\s+", " ", candidate).strip()
        if len(cleaned) >= 10 and "Price" not in cleaned and "Add to cart" not in cleaned and not cleaned.lower().startswith("sponsored"):
            return cleaned

    raw_text = re.sub(r"\s+", " ", " ".join(block.stripped_strings)).strip()
    if not raw_text:
        return ""

    if "Price, product page" in raw_text:
        raw_text = raw_text.split("Price, product page", 1)[0]
    elif "M.R.P:" in raw_text:
        raw_text = raw_text.split("M.R.P:", 1)[0]

    title_text = raw_text.split("Let us know", 1)[-1] if "Let us know" in raw_text else raw_text
    title_text = re.sub(r"Sponsored", " ", title_text, flags=re.I)
    title_text = re.sub(r"\s+", " ", title_text).strip()

    if len(title_text) >= 10 and "You are seeing this ad" not in title_text:
        return title_text

    return ""


def extract_price(block) -> str:
    price_whole = block.find("span", class_="a-price-whole")
    if price_whole:
        whole = price_whole.get_text(" ", strip=True)
        frac = block.find("span", class_="a-price-fraction")
        frac_text = frac.get_text(" ", strip=True) if frac else ""
        return f"{whole}{frac_text}"

    offscreen = block.find("span", class_="a-offscreen")
    if offscreen:
        return offscreen.get_text(" ", strip=True)

    return "N/A"


def extract_rating(block) -> str:
    rating = block.find("span", attrs={"aria-label": re.compile(r"out of 5", re.I)})
    if rating:
        match = re.search(r"(\d+\.\d+)", rating.get("aria-label", ""))
        if match:
            return match.group(1)

    star_tag = block.find("i", class_=lambda x: x and "a-icon-star" in x)
    if star_tag:
        value = star_tag.get_text(" ", strip=True)
        match = re.search(r"(\d+\.\d+)", value)
        if match:
            return match.group(1)

    return "N/A"


def extract_field_from_title(title: str, pattern: str, flags: int = re.I):
    match = re.search(pattern, title, flags)
    return match.group(1) if match else "N/A"


def scrape_amazon_laptops(max_pages: int = 5, output_path: str = str(RAW_PATH)):
    session = requests.Session()
    session.headers.update(HEADERS)
    data = []
    seen_titles = set()

    for page in range(1, max_pages + 1):
        params = {"k": "laptops", "page": page}
        response = session.get(SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        blocks = soup.find_all(attrs={"data-component-type": "s-search-result"})
        if not blocks:
            blocks = soup.find_all("div", class_="s-result-item")

        for block in blocks:
            title = extract_product_title(block)
            if not title or len(title) < 10:
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            price = extract_price(block)
            rating = extract_rating(block)
            brand = re.search(r"^([A-Za-z]+)", title).group(1) if re.search(r"^([A-Za-z]+)", title) else "Unknown"
            ram = extract_field_from_title(title, r"(\d+GB|RAM\s*(\d+GB)?|DDR\d?\s*(\d+GB)?|LPDDR\d?\s*(\d+GB)?)")
            ssd_match = re.search(r"(\d+)\s*(GB|TB)\s*(?:SSD|Storage|HDD)", title, re.I)
            ssd_storage = f"{ssd_match.group(1)}{ssd_match.group(2)}" if ssd_match else "N/A"
            color = extract_field_from_title(title, r"\b(Black|White|Silver|Gray|Grey|Red|Blue|Green|Yellow|Pink|Purple|Gold|Bronze|Rose Gold|Indigo|Glacier)\b")
            processor = "N/A"
            if re.search(r"Apple\s+M\d+", title, re.I):
                processor = re.search(r"Apple\s+M\d+", title, re.I).group(0)
            elif re.search(r"Apple\s+A\d+", title, re.I):
                processor = re.search(r"Apple\s+A\d+", title, re.I).group(0)
            else:
                for keyword in ["Intel", "AMD", "Snapdragon", "MediaTek", "Celeron"]:
                    if re.search(rf"\b{keyword}\b", title, re.I):
                        processor = keyword
                        break

            os_name = "N/A"
            if re.search(r"\b(MacBook|macOS|Mac OS)\b", title, re.I):
                os_name = "MacOS"
            elif re.search(r"\bApple\s+[MA]\d+\b", title, re.I):
                os_name = "MacOS"
            elif re.search(r"\b(Windows|Win\s*11|Win11|Win\s*10|Win10)\b", title, re.I):
                os_name = "Windows"
            else:
                for keyword in ["Linux", "Chrome OS", "Android", "iOS"]:
                    if re.search(rf"\b{keyword}\b", title, re.I):
                        os_name = keyword
                        break

            data.append({
                "title": title,
                "price": clean_price_text(price),
                "brand": brand,
                "ram": ram,
                "ssd_storage": ssd_storage,
                "color": color,
                "processor": processor,
                "os": os_name,
                "rating": rating,
            })

        time.sleep(1)

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    result = scrape_amazon_laptops(max_pages=3)
    print(f"Scraped {len(result)} records into {RAW_PATH}")
