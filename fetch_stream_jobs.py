import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app import create_app
from models import db, JobAd

# Load environment variables from .env file
load_dotenv()

# Get the DATABASE_URL from the environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# Create the Flask app and configure it
app = create_app()

# Stream endpoint for fetching updates to the job ads
stream_url = "https://jobstream.api.jobtechdev.se/stream"

def fetch_stream_jobs():
    # Set the start time as now minus a few minutes
    start_time = (datetime.utcnow() - timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%S')
    
    # Query the stream endpoint for updates since `start_time`
    params = {'date': start_time}
    response = requests.get(stream_url, params=params)
    
    if response.status_code == 200:
        updates = response.json()
        process_updates(updates)
    else:
        print(f"Error fetching updates: {response.status_code}")

def process_updates(updates):
    with app.app_context():
        for update in updates:
            if 'removed' in update and update['removed']:
                remove_job(update['id'])
            else:
                upsert_job(update)
        db.session.commit()

def remove_job(job_id):
    job = JobAd.query.get(job_id)
    if job:
        db.session.delete(job)
        print(f"Ad {job_id} was removed")
    else:
        print(f"Ad {job_id} not found for removal")

def upsert_job(ad):
    job = JobAd.query.get(ad['id'])
    if job:
        update_job(job, ad)
        print(f"Ad {ad['id']} was updated")
    else:
        create_job(ad)
        print(f"Ad {ad['id']} was created")

def update_job(job, ad):
    job.title = ad.get('headline')
    job.description = (ad.get('description') or {}).get('text')
    job.company = (ad.get('employer') or {}).get('name') or job.company
    job.location = (ad.get('workplace_address') or {}).get('municipality')
    job.municipality = (ad.get('workplace_address') or {}).get('municipality')
    job.region = (ad.get('workplace_address') or {}).get('region')
    job.country = (ad.get('workplace_address') or {}).get('country')
    job.employment_type = (ad.get('employment_type') or {}).get('label')
    job.working_hours_type = (ad.get('working_hours_type') or {}).get('label')
    job.salary_type = (ad.get('salary_type') or {}).get('label')
    job.salary_description = ad.get('salary_description')
    job.published_at = datetime.fromisoformat(ad['publication_date']) if ad.get('publication_date') else None
    job.last_application_date = datetime.fromisoformat(ad['application_deadline']).date() if ad.get('application_deadline') else None
    job.application_url = (ad.get('application_details') or {}).get('url')
    job.occupation_group = (ad.get('occupation_group') or {}).get('label')
    job.occupation_field = (ad.get('occupation_field') or {}).get('label')
    job.municipality_concept_id = (ad.get('workplace_address') or {}).get('municipality_concept_id')
    job.region_concept_id = (ad.get('workplace_address') or {}).get('region_concept_id')
    job.country_concept_id = (ad.get('workplace_address') or {}).get('country_concept_id')

def create_job(ad):
    employer = ad.get('employer') or {}
    company_name = employer.get('name') if isinstance(employer, dict) else None
    
    if company_name is None:
        company_name = ad.get('headline', 'Unknown Company').split(' hos ')[-1]
    
    job = JobAd(
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
    db.session.add(job)

if __name__ == '__main__':
    fetch_stream_jobs()