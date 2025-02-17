import os
import requests
import ijson
from app import app, db
from models import JobAd
from datetime import datetime
import time

print("Script started")

# Use Heroku's DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

print(f"Database URL: {DATABASE_URL}")

snapshot_url = "https://jobstream.api.jobtechdev.se/snapshot"

def fetch_snapshot():
    print("Fetching snapshot...")
    try:
        print("Preparing GET request...")
        session = requests.Session()
        session.headers.update({'User-Agent': 'JobboardApp/1.0'})
        
        print(f"Sending GET request to {snapshot_url}...")
        start_time = time.time()
        
        with session.get(snapshot_url, stream=True, timeout=300) as response:  # Increased timeout
            print(f"Received initial response in {time.time() - start_time:.2f} seconds")
            print(f"Response status code: {response.status_code}")
            
            print("Checking response status...")
            response.raise_for_status()
            
            print(f"Response headers: {response.headers}")
            print(f"Response content type: {response.headers.get('Content-Type')}")
            
            print("Processing JSON data...")
            ads = []
            parser = ijson.parse(response.raw)
            
            for prefix, event, value in parser:
                if prefix == 'item' and event == 'start_map':
                    ad = {}
                elif prefix.startswith('item.'):
                    key = prefix.split('.')[1]
                    ad[key] = value
                elif prefix == 'item' and event == 'end_map':
                    ads.append(ad)
                    if len(ads) % 1000 == 0:
                        print(f"Processed {len(ads)} ads")
                        store_ads(ads)
                        ads = []
                    if len(ads) >= 50000:
                        break
            
            if ads:
                store_ads(ads)
            
            print(f"Finished processing ads")
        
    except requests.exceptions.Timeout:
        print("Request timed out. The API might be slow or unresponsive.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def store_ads(ads):
    print(f"Storing {len(ads)} ads...")
    try:
        with app.app_context():
            for ad in ads:
                employer = ad.get('employer') or {}
                company_name = employer.get('name') if isinstance(employer, dict) else None
                
                if company_name is None:
                    company_name = ad.get('headline', 'Unknown Company').split(' hos ')[-1]
                
                job_ad = JobAd(
                    id=ad.get('id'),
                    title=ad.get('headline'),
                    description=(ad.get('description') or {}).get('text'),
                    company=company_name,
                    location=(ad.get('workplace_address') or {}).get('municipality'),
                    municipality=(ad.get('workplace_address') or {}).get('municipality'),
                    region=(ad.get('workplace_address') or {}).get('region'),
                    country=(ad.get('workplace_address') or {}).get('country'),
                    employment_type=(ad.get('employment_type') or {}).get('label'),
                    working_hours_type=(ad.get('working_hours_type') or {}).get('label'),
                    salary_type=(ad.get('salary_type') or {}).get('label'),
                    salary_description=ad.get('salary_description'),
                    published_at=datetime.fromisoformat(ad['publication_date']) if ad.get('publication_date') else None,
                    last_application_date=datetime.fromisoformat(ad['application_deadline']).date() if ad.get('application_deadline') else None,
                    application_url=(ad.get('application_details') or {}).get('url'),
                    occupation_group=(ad.get('occupation_group') or {}).get('label'),
                    occupation_field=(ad.get('occupation_field') or {}).get('label'),
                    municipality_concept_id=(ad.get('workplace_address') or {}).get('municipality_concept_id'),
                    region_concept_id=(ad.get('workplace_address') or {}).get('region_concept_id'),
                    country_concept_id=(ad.get('workplace_address') or {}).get('country_concept_id')
                )
                db.session.merge(job_ad)
            db.session.commit()
        print(f"Stored {len(ads)} ads successfully")
    except Exception as e:
        print(f"An error occurred while storing ads: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

if __name__ == '__main__':
    print("Entering main block")
    fetch_snapshot()
    print("Script finished")