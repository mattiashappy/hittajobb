import os
import uuid
from flask import Flask, request, redirect, url_for, render_template, flash
from models import db, JobAd
from sqlalchemy import or_, func
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Use Heroku's DATABASE_URL or fall back to local database URL
    DATABASE_URL = os.getenv('DATABASE_URL')

    # Heroku's PostgreSQL uses 'postgres://', but SQLAlchemy prefers 'postgresql://'
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Needed for flash messages

    db.init_app(app)

    return app

app = create_app()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    search_query = request.args.get('occupation', '').lower()
    location_query = request.args.get('location', '').lower()

    job_ads_query = JobAd.query

    if search_query:
        job_ads_query = job_ads_query.filter(or_(
            func.lower(JobAd.title).contains(search_query),
            func.lower(JobAd.description).contains(search_query),
            func.lower(JobAd.company).contains(search_query),
            func.lower(JobAd.occupation_group).contains(search_query),
            func.lower(JobAd.occupation_field).contains(search_query)
        ))

    if location_query:
        job_ads_query = job_ads_query.filter(or_(
            func.lower(JobAd.municipality).contains(location_query),
            func.lower(JobAd.region).contains(location_query),
            func.lower(JobAd.country).contains(location_query)
        ))

    total_jobs = job_ads_query.count()

    # Calculate new jobs count for today only
    today = date.today()
    new_jobs_count = job_ads_query.filter(func.date(JobAd.published_at) == today).count()

    job_ads = job_ads_query.order_by(JobAd.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # Get unique locations for autocomplete
    locations = db.session.query(
        func.coalesce(JobAd.municipality, JobAd.region, JobAd.country).label('location')
    ).distinct().order_by('location').all()
    locations = [location[0] for location in locations if location[0]]

    return render_template('index.html', 
                           job_ads=job_ads, 
                           total_jobs=total_jobs, 
                           new_jobs_count=new_jobs_count,
                           locations=locations)

@app.route('/skapa_annons')
def skapa_annons():
    return render_template('skapa_annons.html')

@app.route('/create_ad', methods=['POST'])
def create_ad():
    # Get form data
    job_title = request.form.get('jobTitle')
    company_name = request.form.get('companyName')
    location = request.form.get('location')
    description = request.form.get('description')
    application_url = request.form.get('applicationUrl')

    if job_title and company_name and location and description and application_url:
        # Create a new job ad instance
        new_job_ad = JobAd(
            id=str(uuid.uuid4()),
            title=job_title,
            company=company_name,
            location=location,
            description=description,
            application_url=application_url,
            published_at=datetime.utcnow()
        )

        # Add the new job ad to the database
        db.session.add(new_job_ad)
        db.session.commit()

        # Flash a success message
        flash('Job advertisement successfully created!', 'success')
        return redirect(url_for('index'))
    else:
        # Flash an error message if fields are missing
        flash('Failed to create advertisement. Please fill all fields.', 'danger')
        return redirect(url_for('skapa_annons'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
