from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import random
import csv
import io
from flask import jsonify, Response
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
import re
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION") 
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize the client
client = AzureOpenAI()

# Custom message
custom_message = 'Hi My Name is Nishant, This is My first API call or testing, How are things looking on your end'

# Create the request
# res = client.chat.completions.create(
#     model="gpt-4o",  # Use the correct model, e.g., gpt-4o or gpt-4o-mini
#     messages=[{"role": "system", "content": "You are a helpful assistant."},
#               {"role": "user", "content": custom_message}],
#     temperature=0.7,
#     max_tokens=256,
#     top_p=0.6,
#     frequency_penalty=0.7
# )
# # Access the response correctly
# response = res.choices[0].message.content  # Access content directly
# print(response)

# MySQL database configuration
db_config = {
    'user': 'root',
    'password': 'root1234',
    'host': 'localhost',
    'database': 'skillnavigation'
}
# Connect to the database
db = mysql.connector.connect(**db_config)
cursor = db.cursor()

# Create necessary tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        degree VARCHAR(100),
        specialization VARCHAR(100),
        phone_number VARCHAR(15),
        certifications TEXT,
        internship_details TEXT,
        courses_completed TEXT,
        linkedin_profile VARCHAR(255),
        github_profile VARCHAR(255),
        programming_languages TEXT
    )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT,
    course_completion_percentage DECIMAL(5, 2),
    mcq_score INT,
    project_score INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_type VARCHAR(50),
    data JSON,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS batches (
        id INT AUTO_INCREMENT PRIMARY KEY,
        batch_name VARCHAR(50),
        criteria TEXT,
        min_size INT DEFAULT 25,
        max_size INT DEFAULT 30
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS batch_allocation (
        id INT AUTO_INCREMENT PRIMARY KEY,
        candidate_id INT,
        batch_id INT,
        allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
    )
''')

# Insert Java Batch
cursor.execute(''' 
    INSERT INTO batches (batch_name, criteria, min_size, max_size)
    SELECT * FROM (SELECT 'Java Batch', 'J', 25, 30) AS tmp
    WHERE NOT EXISTS (SELECT 1 FROM batches WHERE batch_name = 'Java Batch')
    LIMIT 1;
''')
db.commit()

# Insert .NET Batch
cursor.execute(''' 
    INSERT INTO batches (batch_name, criteria, min_size, max_size)
    SELECT * FROM (SELECT '.NET Batch', 'N', 25, 30) AS tmp
    WHERE NOT EXISTS (SELECT 1 FROM batches WHERE batch_name = '.NET Batch')
    LIMIT 1;
''')
db.commit()

# Insert Data Engineering Batch
cursor.execute(''' 
    INSERT INTO batches (batch_name, criteria, min_size, max_size)
    SELECT * FROM (SELECT 'Data Engineering Batch', 'D', 25, 30) AS tmp
    WHERE NOT EXISTS (SELECT 1 FROM batches WHERE batch_name = 'Data Engineering Batch')
    LIMIT 1;
''')
db.commit()



cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INT AUTO_INCREMENT PRIMARY KEY,
        candidate_id INT,
        batch_id INT,
        feedback_text TEXT,
        sentiment_score DECIMAL(5, 2),
        provided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
    )
''')

db.commit()

# Endpoints
@app.route('/add_report', methods=['POST'])
def add_report():
    data = request.get_json()
    cursor.execute('''
        INSERT INTO reports (report_type, data)
        VALUES (%s, %s)
    ''', (data['report_type'], data['data']))
    db.commit()
    return jsonify({'message': 'Report added successfully'}), 200

@app.route('/get_reports', methods=['GET'])
def get_reports():
    cursor.execute('SELECT * FROM reports')
    reports = cursor.fetchall()
    result = []
    for report in reports:
        result.append({
            'id': report[0],
            'report_type': report[1],
            'data': report[2],
            'generated_at': report[3]
        })
    return jsonify(result), 200

@app.route('/get_progress', methods=['GET'])
def get_progress():
    cursor.execute('SELECT * FROM progress')
    progress_records = cursor.fetchall()
    result = []
    for record in progress_records:
        result.append({
            'id': record[0],
            'candidate_id': record[1],
            'course_completion_percentage': record[2],
            'mcq_score': record[3],
            'project_score': record[4],
            'updated_at': record[5]
        })
    return jsonify(result), 200

@app.route('/add_progress', methods=['POST'])
def add_progress():
    data = request.get_json()
    cursor.execute('''
        INSERT INTO progress (candidate_id, course_completion_percentage, mcq_score, project_score)
        VALUES (%s, %s, %s, %s)
    ''', (data['candidate_id'], data['course_completion_percentage'], data['mcq_score'], data['project_score']))
    db.commit()
    return jsonify({'message': 'Progress added successfully'}), 200

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    data = request.get_json()
    cursor.execute('''
        INSERT INTO candidates (
            name, email, degree, specialization, phone_number,
            certifications, internship_details, courses_completed,
            linkedin_profile, github_profile, programming_languages
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        data['name'], data['email'], data['degree'], data['specialization'], data['phone_number'],
        data['certifications'], data['internship_details'], data['courses_completed'],
        data['linkedin_profile'], data['github_profile'], data['programming_languages']
    ))
    db.commit()
    return jsonify({'message': 'Candidate added successfully'}), 200

@app.route('/allocate_batch', methods=['POST'])
def allocate_batch():
    data = request.get_json()
    candidate_id = data['candidate_id']
    batch_id = data['batch_id']

    # Check if the candidate is already allocated to a batch
    cursor.execute('SELECT * FROM batch_allocation WHERE candidate_id = %s', (candidate_id,))
    existing_allocation = cursor.fetchone()
    if existing_allocation:
        return jsonify({'error': 'Candidate is already allocated to a batch'}), 400

    # Check if the batch has space (based on max_size)
    cursor.execute('SELECT COUNT(*) FROM batch_allocation WHERE batch_id = %s', (batch_id,))
    batch_size = cursor.fetchone()[0]

    cursor.execute('SELECT max_size FROM batches WHERE id = %s', (batch_id,))
    max_size = cursor.fetchone()[0]

    if batch_size >= max_size:
        return jsonify({'error': 'Batch is full'}), 400

    # Allocate the candidate to the batch
    cursor.execute('''
        INSERT INTO batch_allocation (candidate_id, batch_id)
        VALUES (%s, %s)
    ''', (candidate_id, batch_id))
    db.commit()

    return jsonify({'message': 'Candidate allocated to batch successfully'}), 200

@app.route('/get_batches', methods=['GET'])
def get_batches():
    cursor.execute('SELECT * FROM batches')
    batches = cursor.fetchall()
    result = []
    for batch in batches:
        result.append({
            'id': batch[0],
            'batch_name': batch[1],
            'criteria': batch[2],
            'min_size': batch[3],
            'max_size': batch[4]
        })
    return jsonify(result), 200

@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    data = request.get_json()
    cursor.execute('''
        INSERT INTO feedback (candidate_id, batch_id, feedback_text, sentiment_score)
        VALUES (%s, %s, %s, %s)
    ''', (data['candidate_id'], data['batch_id'], data['feedback_text'], data['sentiment_score']))
    db.commit()
    return jsonify({'message': 'Feedback added successfully'}), 200

@app.route('/get_feedback', methods=['GET'])
def get_feedback():
    cursor.execute('SELECT * FROM feedback')
    feedback_list = cursor.fetchall()
    result = []
    for feedback in feedback_list:
        result.append({
            'id': feedback[0],
            'candidate_id': feedback[1],
            'batch_id': feedback[2],
            'feedback_text': feedback[3],
            'sentiment_score': feedback[4],
            'provided_at': feedback[5]
        })
    return jsonify(result), 200

@app.route('/get_candidates', methods=['GET'])
def get_candidates():
    cursor.execute('SELECT * FROM candidates')
    candidates = cursor.fetchall()
    result = []
    for candidate in candidates:
        result.append({
            'id': candidate[0],
            'name': candidate[1],
            'email': candidate[2],
            'degree': candidate[3],
            'specialization': candidate[4],
            'phone_number': candidate[5],
            'certifications': candidate[6],
            'internship_details': candidate[7],
            'courses_completed': candidate[8],
            'linkedin_profile': candidate[9],
            'github_profile': candidate[10],
            'programming_languages': candidate[11]
        })
    return jsonify(result), 200

@app.route('/get_batch_allocation', methods=['GET'])
def get_batch_allocation():
    cursor.execute('''
        SELECT 
            c.id, c.name, c.email, c.phone_number, b.batch_name
        FROM 
            candidates c
        LEFT JOIN 
            batch_allocation ba ON c.id = ba.candidate_id
        LEFT JOIN 
            batches b ON ba.batch_id = b.id
    ''')

    candidates = cursor.fetchall()
    result = []

    for candidate in candidates:
        result.append({
            'id': candidate[0],
            'name': candidate[1],
            'email': candidate[2],
            'phone_number': candidate[3],
            'batch_name': candidate[4] if candidate[4] else 'Not Allocated'
        })

    return jsonify(result), 200



@app.route('/allocate_random_batch', methods=['POST'])
def allocate_random_batch():
    # Step 1: Get candidates who are not allocated to any batch
    cursor.execute(''' 
        SELECT id FROM candidates
        WHERE id NOT IN (SELECT candidate_id FROM batch_allocation)
    ''')
    candidates = cursor.fetchall()

    if not candidates:
        return jsonify({'message': 'No candidates available for allocation'}), 400

    # Step 2: Get all batches and their maximum sizes
    cursor.execute('SELECT id, batch_name, max_size FROM batches')
    batches = cursor.fetchall()

    # Step 3: Prepare to allocate candidates to batches
    batch_allocations = []

    for candidate in candidates:
        candidate_id = candidate[0]

        # Randomly select a batch (with available space)
        available_batches = []

        for batch in batches:
            batch_id, batch_name, max_size = batch
            cursor.execute('SELECT COUNT(*) FROM batch_allocation WHERE batch_id = %s', (batch_id,))
            batch_size = cursor.fetchone()[0]

            # Only consider batches that are not full
            if batch_size < max_size:
                available_batches.append(batch)

        if not available_batches:
            continue  # Skip the candidate if no batch has space left

        # Randomly select one batch from the available batches
        selected_batch = random.choice(available_batches)
        batch_id = selected_batch[0]

        # Allocate the candidate to the batch
        batch_allocations.append((candidate_id, batch_id))

    # If there are any allocations, insert them into the database
    if batch_allocations:
        cursor.executemany('''
            INSERT INTO batch_allocation (candidate_id, batch_id)
            VALUES (%s, %s)
        ''', batch_allocations)
        db.commit()

    # Return a message indicating how many candidates were allocated
    return jsonify({'message': f'{len(batch_allocations)} candidates allocated to batches successfully'}), 200

import json
import re
from flask import jsonify
import csv
import io
import re
from flask import jsonify
import csv
import io
import re
from flask import jsonify

@app.route('/allocate_all_candidates_batch', methods=['POST'])
def allocate_all_candidates_batch():
    # Step 1: Fetch candidate details from the database (ID, skills, courses, languages)
    cursor.execute('''SELECT id, programming_languages, courses_completed, certifications
                      FROM candidates WHERE id NOT IN (SELECT candidate_id FROM batch_allocation) ''')
    candidates = cursor.fetchall()

    if not candidates:
        return jsonify({'error': 'No candidates found'}), 400

    # Step 2: Format data for the AI to decide batch allocation
    candidate_data = []
    for candidate in candidates:
        candidate_id, programming_languages, courses_completed, certifications = candidate
        candidate_data.append({
            'candidate_id': candidate_id,
            'skills': programming_languages,
            'courses': courses_completed,
            'languages': certifications
        })

    # Step 3: Make a single request to the OpenAI API for batch allocation
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use the correct model
            messages=[{"role": "system", "content": "You are a helpful assistant that allocates candidates to batches."},
                      {"role": "user", "content": f"for each candidate, must assign a suitable batch id based on skills, courses, and certifications between id 1:Java, id 2:.Net, id 3:Data Engineering in the form of CSV without header and next line (also without any explanations)\n\n{candidate_data}"}],
            temperature=0.7,
            max_tokens=1024,
            top_p=0.6,
            frequency_penalty=0.7
        )

        allocations_data = response.choices[0].message.content.strip()
        print('TEST0\n', allocations_data, '\nTEST0 END\n')

        # Step 4: Process the AI's response and parse CSV
       # Clean up excessive spaces
        allocations_csv = io.StringIO(allocations_data)
        print('TEST1\n', allocations_csv, '\nTEST1 END\n')
        csv_reader = csv.reader(allocations_csv)
        print('TEST2\n', csv_reader, '\nTEST2 END\n')

        # Skip the header row if present (check for known headers)
        header = next(csv_reader)
        if 'candidate_id' in header and 'batch_id' in header:
            print("Header detected, skipping.")
        else:
            # If no header found, process first row as data
            allocations_csv.seek(0)  # Rewind the StringIO object
            csv_reader = csv.reader(allocations_csv)

        allocations = []
        for row in csv_reader:
            try:
                # Skip empty or invalid rows
                if len(row) < 2 or not row[0].strip() or not row[1].strip():
                    continue

                candidate_id = row[0].strip()  # Clean candidate_id
                batch_id = row[1].strip()  # Clean batch_id

                # Skip rows where batch_id is invalid
                if batch_id == "N/A" or not batch_id:
                    continue

                candidate_id = int(candidate_id)  # Convert to integer
                batch_id = int(batch_id)  # Convert to integer

                # Append valid allocation
                allocations.append((candidate_id, batch_id))

            except ValueError as e:
                print(f"Skipping invalid row: {row}, Error: {e}")
                continue

        print("TEST3\n", allocations, '\nTEST3 END\n')

        # Step 5: Insert batch allocations into the database
        if allocations:
            cursor.executemany('''
                INSERT INTO batch_allocation (candidate_id, batch_id)
                VALUES (%s, %s)
            ''', allocations)
            db.commit()

        return jsonify({'message': f'{len(allocations)} candidates allocated to batches successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Error processing AI response: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)

