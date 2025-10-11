from langchain_tavily import TavilySearch
import json
import requests
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
load_dotenv(".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def get_tool():
    tool = TavilySearch(
        max_results=5,
        topic="general",
        include_answer="advanced",
    )
    return tool

def call_on_tavily(query: str, id: str = "1"):
    tool = get_tool()
    model_generated_tool_call = {
        "args": {"query": query},
        "id": id,
        "name": "tavily",
        "type": "tool_call",
    }
    tool_msg = tool.invoke(model_generated_tool_call)
    ans = json.loads(tool_msg.content)
    time.sleep(1)
    return ans


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

def get_tavily_all_champions_personality(limit: Optional[int] = None) -> List[Dict[str, str]]:      
    titles = fetch_character_titles_from_category(CATEGORY_TITLE)
    all_champions = []
    for i, t in enumerate(titles):
        if limit and i >= limit:
            break
        title = t
        query = f"In league of legends lore, what is {title}'s personality like?"
        response = call_on_tavily(query)
        personality = response.get("answer", "").strip()
        champ_info = {
            "name": title,
            "personality": personality
        }
        all_champions.append(champ_info)
        time.sleep(1)  # To avoid hitting rate limits
    return all_champions

def get_tavily_all_champions(
    limit: Optional[int] = None,
    background: bool = False,
    personality: bool = False,
    appearance: bool = False
) -> List[Dict[str, str]]:
    """
    Fetches champion info from Tavily. You can toggle background, personality, 
    and/or appearance using boolean flags.
    """
    titles = fetch_character_titles_from_category(CATEGORY_TITLE)
    all_champions = []

    for i, t in enumerate(titles):
        if limit and i >= limit:
            break

        champ_info = {"name": t}

        if background:
            query = f"In league of legends lore, who is {t} and what is their background story (biography)?"
            response = call_on_tavily(query)
            champ_info["background"] = response.get("answer", "").strip()

        if personality:
            query = f"In league of legends lore, what is {t}'s personality like?"
            response = call_on_tavily(query)
            champ_info["personality"] = response.get("answer", "").strip()

        if appearance:
            query = f"In league of legends lore, what is {t}'s appearance like?"
            response = call_on_tavily(query)
            champ_info["appearance"] = response.get("answer", "").strip()

        all_champions.append(champ_info)
        # time.sleep(1)  # avoid rate limits

    return all_champions

if __name__ == "__main__":
    champions = get_tavily_all_champions(
        limit=5,
        background=True,
        personality=True,
        appearance=True
    )
    out_path = "champion_characters_tavily.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(champions, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(champions)} entries to {out_path}")

# it would be a better idea to call the tavily api and save each character 
# instead of calling on all characters at once and saving them all at once
# because if the script fails halfway through, we would lose all the data
# instead of just losing the data for the characters that failed