from flask import Flask, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import requests
import datetime
import csv
import io

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Retrieve the database configuration from the environment
URI = os.getenv("URL")
SDWAN_URL = os.getenv("SDWAN_URL")
app = Flask(__name__)

# prepare SQLAlchemy DB
# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = URI; #'postgresql://username:password@localhost:5432/alerts_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Define database models
class PolicyIndex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index_no = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(12), nullable=False)  # YYYYMMDDHHMM

class PolicyRoute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index_no = db.Column(db.Integer, nullable=True)
    policy_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    mode = db.Column(db.String(50), nullable=True)
    owner = db.Column(db.String(100), nullable=False)
    reference_count = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.String(12), nullable=False)  # YYYYMMDDHHMM


with app.app_context():
    db.create_all()


def get_next_policy_index():
    """Retrieve and update the policy index counter."""
    index_record = PolicyIndex.query.order_by(PolicyIndex.id.desc()).first()
    if index_record:
        new_index = index_record.index_no + 1 if index_record.index_no < 10000 else 1
    else:
        new_index = 1

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    
    new_index_record = PolicyIndex(index_no=new_index, timestamp=timestamp)
    db.session.add(new_index_record)
    db.session.commit()
    
    return new_index

def fetch_policy_data():
    """Fetch policy information from the given API endpoint."""
    url = SDWAN_URL
    response = requests.get(url, verify=False)  # SSL verification disabled for local testing
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/policy/pullpolicymetrics', methods=['GET'])
def pull_policy_metrics():
    index_no = get_next_policy_index()

    # Clear previous entries for this index
    PolicyRoute.query.filter_by(index_no=index_no).delete()
    
    policy_data = fetch_policy_data()
    if not policy_data:
        return jsonify({'error': 'Failed to fetch policy data'}), 500

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")

    try:
        policies = policy_data.get("result", {}).get("data", [])
        for policy in policies:
            policy_id = policy.get("definitionId")
            name = policy.get("name")
            policy_type = policy.get("type")
            description = policy.get("description", "")
            mode = policy.get("mode", "")
            owner = policy.get("owner")
            reference_count = policy.get("referenceCount", 0)
            last_updated_unix = policy.get("lastUpdated", 0)

            # Convert UNIX timestamp to YYYYMMDDHHMM
            last_updated = datetime.datetime.utcfromtimestamp(last_updated_unix / 1000).strftime("%Y%m%d%H%M")

            policy_entry = PolicyRoute(
                index_no=index_no,
                policy_id=policy_id,
                name=name,
                type=policy_type,
                description=description,
                mode=mode,
                owner=owner,
                reference_count=reference_count,
                last_updated=last_updated
            )
            db.session.add(policy_entry)

        db.session.commit()
        return jsonify({'message': 'Policy data updated successfully', 'index': index_no}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/policy/exportcsv', methods=['GET'])
def export_policy_data_csv():
    """Exports the latest 1000 records for policies in CSV format."""
    records = (PolicyRoute.query
               .order_by(PolicyRoute.id.desc())
               .limit(1000)
               .all())

    if not records:
        return jsonify({'error': 'No records found'}), 404

    # Create CSV in-memory
    output = io.StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(["Index", "Policy ID", "Name", "Type", "Description", 
                         "Mode", "Owner", "Reference Count", "Last Updated"])
    
    # Write data
    for record in records:
        csv_writer.writerow([
            record.index_no,
            record.policy_id,
            record.name,
            record.type,
            record.description,
            record.mode,
            record.owner,
            record.reference_count,
            record.last_updated
        ])
    
    output.seek(0)

    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=policy_data.csv"})

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
