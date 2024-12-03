from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from .logic import CommentAnalyzer

main = Blueprint('main', __name__)
analyzer = CommentAnalyzer()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/save_settings', methods=['POST'])
def save_settings():
    try:
        data = request.json
        analyzer.save_settings(
            data['html_name'],
            data['email_types'],
            data['pick_number'],
            data['grace_period']
        )
        return jsonify({"message": "Settings saved successfully"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@main.route('/get_comments', methods=['GET'])
def get_comments():
    try:
        comments = analyzer.get_comments()
        return jsonify(comments)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

@main.route('/overdue_comments', methods=['POST'])
def overdue_comments():
    try:
        data = request.json
        comments = analyzer.get_comments()
        end_date = data['end_date']
        comments_remove_overdue, comments_overdue, cnt_overdue, cnt_not_overdue = analyzer.overdue_comments(comments, end_date)
        return jsonify({
            "comments_remove_overdue": comments_remove_overdue,
            "comments_overdue": comments_overdue,
            "cnt_overdue": cnt_overdue,
            "cnt_not_overdue": cnt_not_overdue
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        print("route overdue comment called")
        return jsonify({"error": str(e)}), 400

@main.route('/find_email', methods=['POST'])
def find_email():
    data = request.json
    comments_remove_overdue = data['comments_remove_overdue']
    comments_emails, cnt_email = analyzer.find_email(comments_remove_overdue)
    return jsonify({
        "comments_emails": comments_emails,
        "cnt_email": cnt_email
    })

@main.route('/find_duplicate_comments', methods=['POST'])
def find_duplicate_comments():
    data = request.json
    comments_emails = data['comments_emails']
    comments_remove_duplicate, duplicate_emails, cnt_duplicate, cnt_not_duplicate = analyzer.find_duplicate_comments(comments_emails)
    return jsonify({
        "comments_remove_duplicate": comments_remove_duplicate,
        "duplicate_emails": duplicate_emails,
        "cnt_duplicate": cnt_duplicate,
        "cnt_not_duplicate": cnt_not_duplicate
    })

@main.route('/random_picker', methods=['POST'])
def random_picker():
    try:
        data = request.json
        comments_remove_duplicate = data['comments_remove_duplicate']
        pick_number = data['pick_number']
        random_emails = analyzer.random_picker(comments_remove_duplicate, pick_number)
        return jsonify(random_emails)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@main.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.html'):
        filename = "comments.html" # change filename to comments.html
        file.save(os.path.join('uploads', filename))
        analyzer.html_name = os.path.join('uploads', filename)
        return jsonify({"message": "File uploaded successfully"})
    else:
        return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    main.run(debug=True)