import requests
from datetime import datetime, timedelta

class FootballAPI:
    def __init__(self):
        self.base_url = "https://www.fotmob.com/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        # Add cache-busting timestamp
        params["_"] = int(datetime.now().timestamp() * 1000)
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error ({url}): {e}")
            return None

    def get_leagues(self):
        # IDs for FotMob (Top 5)
        return [
            {"id": 47, "name": "Premier League", "country": "England"},
            {"id": 87, "name": "La Liga", "country": "Spain"},
            {"id": 54, "name": "Bundesliga", "country": "Germany"},
            {"id": 55, "name": "Serie A", "country": "Italy"},
            {"id": 53, "name": "Ligue 1", "country": "France"}
        ]

    def get_standings(self, league_id):
        data = self._get("leagues", {"id": league_id})
        standings = []
        if data and "table" in data and data["table"]:
            tables = data["table"][0]["data"]["table"]["all"]
            for row in tables:
                standings.append({
                    "rank": row["idx"],
                    "name": row["name"],
                    "played": row["played"],
                    "pts": row["pts"],
                    "gd": row["goalConDiff"]
                })
        return standings

    def get_teams(self, league_id):
        data = self._get("leagues", {"id": league_id})
        teams = []
        if data and "table" in data and data["table"]:
            tables = data["table"][0]["data"]["table"]["all"]
            for row in tables:
                teams.append({
                    "id": row["id"],
                    "name": row["name"]
                })
        return teams

    def get_matches(self, team_id, status_group):
        data = self._get("teams", {"id": team_id})
        matches = []
        
        if data and "fixtures" in data:
            all_fixtures = data["fixtures"].get("allFixtures", {}).get("fixtures", [])
            for m in all_fixtures:
                status_obj = m.get("status", {})
                is_finished = status_obj.get("finished", False)
                is_started = status_obj.get("started", False)
                is_cancelled = status_obj.get("cancelled", False)
                score_str = status_obj.get("scoreStr", "v")
                
                home_name = m["home"]["name"]
                away_name = m["away"]["name"]
                
                if is_finished and (not score_str or score_str == "v"):
                     score_str = f"{m.get('home', {}).get('score', 0)} - {m.get('away', {}).get('score', 0)}"

                # Robust live_time extraction
                lt = status_obj.get("liveTime", {})
                live_time = lt.get("short") or lt.get("long") or status_obj.get("reason", {}).get("short", "")
                if live_time:
                    # Clean unicode chars
                    live_time = live_time.replace('\u200e', '').replace('\u2019', '')
                
                if live_time and ":" in live_time:
                    live_time = live_time.split(":")[0]

                match_info = {
                    "id": m["id"],
                    "date": status_obj.get("utcTime"), 
                    "home": home_name,
                    "away": away_name,
                    "status": "Live" if is_started and not is_finished else ("Finished" if is_finished else "Upcoming"),
                    "score": score_str,
                    "match_time": live_time
                }
                
                if status_group == "live":
                    if is_started and not is_finished:
                        matches.append(match_info)
                elif status_group == "upcoming":
                    if not is_started and not is_finished and not is_cancelled:
                         matches.append(match_info)
                elif status_group == "past":
                    if is_finished:
                        matches.append(match_info)

        if status_group == "past":
            return matches[-5:] if matches else []
        return matches[:5]

    def get_match_events(self, match_id):
        data = self._get("matchDetails", {"matchId": match_id})
        goals = []
        if not data or "content" not in data or "matchFacts" not in data["content"]:
            return goals

        events_container = data["content"]["matchFacts"].get("events")
        if not events_container:
            return goals

        events = []
        if isinstance(events_container, dict):
             events = events_container.get("events", [])
        elif isinstance(events_container, list):
             events = events_container

        for event in events:
            if event.get("type") == "Goal":
                player_name = event.get("player", {}).get("name", "Unknown")
                time = event.get("timeStr", str(event.get("time", "")))
                goals.append(f"{player_name} ({time}')")
        return goals

    def get_all_matches(self, date_str=None):
        dates = []
        if not date_str:
            today = datetime.now()
            dates = [
                (today - timedelta(days=2)).strftime("%Y%m%d"),
                (today - timedelta(days=1)).strftime("%Y%m%d"),
                today.strftime("%Y%m%d"),
                (today + timedelta(days=1)).strftime("%Y%m%d")
            ]
        else:
            dates = [date_str]
        
        # Load Top 5 Team IDs
        try:
            import json
            import os
            path = os.path.join(os.path.dirname(__file__), "top_5_teams.json")
            with open(path, "r") as f:
                TOP_5_TEAM_IDS = set(json.load(f))
        except:
            print("Warning: Could not load top_5_teams.json")
            TOP_5_TEAM_IDS = set()
            
        all_matches = []
        for d in dates:
            data = self._get("data/matches", {"date": d})
            
            if data and "leagues" in data:
                for league in data["leagues"]:
                    league_name = league.get("name", "Unknown")
                    league_id = league.get("id")
                    
                    # Check each match in every league (Champions League, Cup, etc included)
                    for m in league.get("matches", []):
                        home_id = m.get("home", {}).get("id")
                        away_id = m.get("away", {}).get("id")
                        
                        # Filter: Match must involve at least one Top 5 Team
                        if home_id not in TOP_5_TEAM_IDS and away_id not in TOP_5_TEAM_IDS:
                           continue
                            
                        status_obj = m.get("status", {})
                        is_live = status_obj.get("started", False) and not status_obj.get("finished", False)
                        is_finished = status_obj.get("finished", False)
                        
                        lt = status_obj.get("liveTime", {})
                        live_time = lt.get("short") or lt.get("long") or status_obj.get("reason", {}).get("short", "")
                        
                        if live_time:
                             live_time = live_time.replace('\u200e', '').replace('\u2019', '')

                        if live_time and ":" in live_time:
                            live_time = live_time.split(":")[0]
                        
                        all_matches.append({
                            "id": m.get("id"),
                            "home": m.get("home", {}).get("name"),
                            "away": m.get("away", {}).get("name"),
                            "home_id": home_id,
                            "away_id": away_id,
                            "score": status_obj.get("scoreStr", "v"),
                            "status_text": status_obj.get("reason", {}).get("short", ""),
                            "is_live": is_live,
                            "is_finished": is_finished,
                            "league": league_name,
                            "league_id": league_id,
                            "match_time": live_time
                        })
        return all_matches
