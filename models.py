from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class JobAd(db.Model):
    __tablename__ = 'job_ads'
    
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    municipality = db.Column(db.String(255))
    region = db.Column(db.String(255))
    country = db.Column(db.String(255))
    employment_type = db.Column(db.String(100))
    working_hours_type = db.Column(db.String(100))
    salary_type = db.Column(db.String(100))
    salary_description = db.Column(db.Text)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_application_date = db.Column(db.Date)
    application_url = db.Column(db.String(500))
    occupation_group = db.Column(db.String(255))
    occupation_field = db.Column(db.String(255))
    municipality_concept_id = db.Column(db.String(255))
    region_concept_id = db.Column(db.String(255))
    country_concept_id = db.Column(db.String(255))

    def __repr__(self):
        return f'<JobAd {self.id} {self.title}>'

def init_db(app):
    with app.app_context():
        db.Model.metadata.create_all(bind=db.engine, checkfirst=True)