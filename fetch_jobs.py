import requests
import json

# Snapshot endpoint for fetching all currently open job ads
snapshot_url = "https://jobstream.api.jobtechdev.se/snapshot"

def fetch_snapshot():
    response = requests.get(snapshot_url)
    if response.status_code == 200:
        ads = response.json()
        store_ads(ads)
    else:
        print(f"Error fetching snapshot: {response.status_code}")

def store_ads(ads):
    # Save the ads to a file or database (for now we just print the count)
    with open("job_ads_snapshot.json", "w") as f:
        json.dump(ads, f)
    print(f"Snapshot fetched. Total ads: {len(ads)}")

if __name__ == '__main__':
    fetch_snapshot()
