import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv("config.env")

API_KEY = os.getenv("FOOTBALL_API_KEY")
TEAM_ID = 86  # Real Madrid ID
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

_last_score = None  # avvalgi hisobni eslab turish


async def get_next_matches():
    """Kelgusi Real Madrid o‘yinlarini olish"""
    url = f"{BASE_URL}/teams/{TEAM_ID}/matches?status=SCHEDULED"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()

    matches = []
    for match in data.get("matches", [])[:3]:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        date = datetime.datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
        competition = match["competition"]["name"]

        matches.append({
            "home": home,
            "away": away,
            "date": date,
            "competition": competition
        })
    return matches


async def get_live_match():
    """Agar Real Madrid jonli o‘yinda bo‘lsa, holatini qaytaradi"""
    global _last_score

    url = f"{BASE_URL}/teams/{TEAM_ID}/matches?status=LIVE"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()

    matches = data.get("matches", [])
    if not matches:
        return None, False  # o‘yin yo‘q, gol yo‘q

    match = matches[0]
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    score = match["score"]

    current_score = f"{score['fullTime']['home'] or 0}-{score['fullTime']['away'] or 0}"

    # Gollarni jonli kuzatish uchun "halfTime" emas, "live" dan foydalanamiz
    full_home = score.get("fullTime", {}).get("home") or 0
    full_away = score.get("fullTime", {}).get("away") or 0
    half_home = score.get("halfTime", {}).get("home") or 0
    half_away = score.get("halfTime", {}).get("away") or 0

    # Avvalgi hisobdan farq bo‘lsa, bu gol degani
    goal_detected = False
    if _last_score and _last_score != current_score:
        goal_detected = True

    _last_score = current_score

    return {
        "home": home,
        "away": away,
        "score": current_score,
        "competition": match["competition"]["name"],
    }, goal_detected
