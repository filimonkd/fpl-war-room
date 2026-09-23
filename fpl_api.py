import requests
import time

BASE_URL = "https://fantasy.premierleague.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_league_standings(league_id):
    url = f"{BASE_URL}/leagues-classic/{league_id}/standings/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching league {league_id}: {e}")
        return None

def get_bootstrap_data():
    url = f"{BASE_URL}/bootstrap-static/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bootstrap data: {e}")
        return None

def get_entry_picks(entry_id, gameweek):
    url = f"{BASE_URL}/entry/{entry_id}/event/{gameweek}/picks/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def get_entry_live(entry_id):
    """Fetches live entry data including squad value, bank, and live points."""
    url = f"{BASE_URL}/entry/{entry_id}/live/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def get_fixtures():
    """Fetches all fixtures for FDR calculation."""
    url = f"{BASE_URL}/fixtures/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None
def get_entry_history(entry_id):
    """Fetches the full gameweek-by-gameweek history and chip usage for a manager."""
    url = f"{BASE_URL}/entry/{entry_id}/history/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None