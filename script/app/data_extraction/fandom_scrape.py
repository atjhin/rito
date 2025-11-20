import time
import json
import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup, Tag

BASE = "https://leagueoflegends.fandom.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LoL-LoreScraper/1.1; +https://example.com/contact)",
    "Accept-Language": "en-US,en;q=0.9",
}

CATEGORY_TITLE = "Category:Characters_in_League_of_Legends"
MW_API = f"{BASE}/api.php"

# --- HTTP helper with simple retry ---
def get(url: str, *, params=None, retries=3, sleep=1.0) -> requests.Response:
    for i in range(retries):
        r = requests.get(url, headers=HEADERS, params=params, timeout=25)
        if r.status_code == 200:
            return r
        if i < retries - 1:
            time.sleep(sleep * (i + 1))
    r.raise_for_status()
    return r

# --- 1) Get ALL Character pages from the category via MediaWiki API (no infinite scroll headaches) ---
def fetch_character_titles_from_category(category_title: str) -> List[str]:
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_title,
        "cmlimit": "500",
        "cmtype": "page",
        "format": "json",
    }
    while True:
        data = get(MW_API, params=params).json()
        for item in data["query"]["categorymembers"]:
            titles.append(item["title"])  # e.g., "Aatrox"
        if "continue" in data:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
        else:
            break
    return titles

# --- Utilities ---
SECTION_BG_CANDIDATES = [
    "background", "biography", "lore", "history", "story", "backstory"
]
SECTION_PERS_CANDIDATES = [
    # Avoid matching generic words like "character"/"characteristics"
    # which often appear as infobox headings ("Characteristics") and pull
    # structured infobox data. Prefer explicit personality-related headings.
    "personality", "traits", "temperament", "quirks", "mannerisms"
]

SECTION_APPEARANCE_CANDIDATES = [
    "appearance", "looks", "physical description", "physical characteristics"
]

def norm_text(s: str) -> str:
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def heading_text(h: Tag) -> str:
    span = h.find(class_="mw-headline")
    return (span.get_text(strip=True) if span else h.get_text(strip=True)).strip()

def extract_named_section(soup: BeautifulSoup, names: List[str]) -> Optional[str]:
    """Find the FIRST h2/h3 whose text matches any candidate, then gather text until next h2/h3."""
    root = soup.select_one(".mw-parser-output") or soup
    headers = root.select("h2, h3")
    target = None
    for h in headers:
        title = heading_text(h).lower()
        if any(n in title for n in names):
            target = h
            break
    if not target:
        return None
    parts = []
    # Stop only at the next top-level section (h2). Many pages use h3/h4 for
    # subsections (e.g. "Background" -> "Early Life", "Ascension"), so
    # collecting until the next h2 captures those nested paragraphs as well.
    for sib in target.find_next_siblings():
        if sib.name == "h2":
            break
        # Keep only content-ish nodes; allow divs too (some pages wrap text)
        # But skip MediaWiki/Fandom infobox items which use classes like
        # "pi-item"/"pi-data" (they are not section body text).
        if sib.name in {"p", "ul", "ol", "blockquote", "div"}:
            cls = sib.get("class") or []
            if any(str(c).startswith("pi-") for c in cls):
                # skip infobox/data card entries
                continue
            for sup in sib.select("sup, .mw-editsection"):
                sup.decompose()
            txt = sib.get_text(" ", strip=True)
            if txt:
                parts.append(txt)
    return norm_text("\n\n".join(parts)) if parts else None

def is_champion_page(soup: BeautifulSoup, title: str) -> bool:
    """Champion Character pages usually link to <Name>/LoL in the infobox area."""
    base = title.replace(" ", "_")
    lo_link = f"/wiki/{base}/LoL"
    # common places: infobox or "Champion" row
    return bool(soup.select_one(f'a[href="{lo_link}"]'))

def scrape_character_page(title: str) -> Optional[Dict]:
    url = f"{BASE}/wiki/{title.replace(' ', '_')}"
    html = get(url).text
    soup = BeautifulSoup(html, "html.parser")

    # Skip non-champ characters if you only want champions
    if not is_champion_page(soup, title):
        return None

    h1 = soup.find("h1", id="firstHeading")
    page_title = h1.get_text(strip=True) if h1 else title
    background = extract_named_section(soup, SECTION_BG_CANDIDATES)
    personality = extract_named_section(soup, SECTION_PERS_CANDIDATES)
    appearance = extract_named_section(soup, SECTION_APPEARANCE_CANDIDATES)

    # Parse portable-infobox data (pi-item pi-data) into a small dict
    infobox = {}
    infobox_root = soup.select_one('.portable-infobox')
    if infobox_root:
        for item in infobox_root.select('.pi-item.pi-data'):
            # label in .pi-data-label, value in .pi-data-value (or text)
            label_el = item.select_one('.pi-data-label')
            value_el = item.select_one('.pi-data-value')
            label = label_el.get_text(' ', strip=True) if label_el else None
            value = value_el.get_text(' ', strip=True) if value_el else item.get_text(' ', strip=True)
            if label:
                infobox[label] = value

    return {
        "name": page_title,
        "url": url,
        "infobox": infobox,
        "background": background or "",
        "personality": personality or "",
        "appearance": appearance or "",
    }

def scrape_all_champions(limit: Optional[int] = None) -> List[Dict]:
    titles = fetch_character_titles_from_category(CATEGORY_TITLE)
    out = []
    for i, t in enumerate(titles):
        if limit and i >= limit:
            break
        try:
            row = scrape_character_page(t)
            if row:
                out.append(row)
        except Exception as e:
            print(f"[warn] {t}: {e}")
        time.sleep(0.3)  # be polite
    return out

if __name__ == "__main__":
    data = scrape_all_champions(limit=10)  # remove limit to get them all (~179 chars, many are champs)
    out_path = "champion_characters.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(data)} entries to {out_path}")
