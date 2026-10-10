counter_url = "https://deinserver.de/counter.php"  # <-- hier anpassen

# Install-Counter abrufen
try:
    res_counter = requests.get(counter_url, timeout=5)
    if res_counter.status_code == 200:
        install_count = int(res_counter.text.strip())
        print(f"DEBUG: Installationen: {install_count}")
        total_stats += install_count
except Exception as e:
    print("DEBUG: Counter Fehler:", e)
