from api import FootballAPI

def test_api_standings():
    print("--- Testing API Standings (GD) ---")
    api = FootballAPI()
    try:
        standings = api.get_standings(47) # Premier League
        if standings:
            first = standings[0]
            print(f"First Row Keys: {first.keys()}")
            if 'gd' in first:
                print(f"[PASS] 'gd' found in standings: {first['gd']}")
            else:
                print(f"[FAIL] 'gd' NOT found in standings.")
            
            # Simulate Table Print
            print("\n--- Simulated Table Output ---")
            print(" # Team       P  GD Pts")
            print("-----------------------")
            for row in standings[:5]:
                rank = str(row['rank']).rjust(2)
                name = row['name'][:10].ljust(11) 
                played = str(row['played']).rjust(2)
                gd = str(row.get('gd', 0)).rjust(3)
                pts = str(row['pts']).rjust(3)
                print(f"{rank} {name}{played} {gd} {pts}")
        else:
            print("[WARNING] No standings returned.")
    except Exception as e:
        print(f"[ERROR] {e}")

def test_time_parsing():
    print("\n--- Testing Time Logic ---")
    # Logic copied from api.py
    scenarios = ["45:00", "45+2:00", "90:15", "12", "HT"]
    for s in scenarios:
        live_time = s
        if live_time and ":" in live_time:
            live_time = live_time.split(":")[0]
        
        # Logic from handlers.py
        display = live_time
        if display and display[0].isdigit():
            display += "'"
            
        print(f"Original: {s.ljust(10)} -> Parsed: {live_time.ljust(8)} -> Display: {display}")

if __name__ == "__main__":
    test_api_standings()
    test_time_parsing()
