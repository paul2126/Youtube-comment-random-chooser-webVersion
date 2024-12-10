from datetime import datetime
import json
from urllib.parse import urlencode
from flask import Blueprint, flash, render_template, request, jsonify, send_from_directory, url_for
from flask_login import current_user, login_required, login_manager, login_user, logout_user
from werkzeug.utils import secure_filename
import os
from .logic import CommentAnalyzer
from .exception import SuccessException

from flask import request #회원정보 제출했을때 받아오기 위한 request, post요청을 활성화시키기 위함
from flask import redirect   #페이지 이동시키는 함수
from app.forms import RegisterForm
from app.forms import LoginForm
from app.models import Fcuser #모델의 클래스 가져오기.
from app.models import db
from flask import session 

main = Blueprint('main', __name__)
analyzer = CommentAnalyzer()

@main.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', username=current_user.username)
    else:
        form = LoginForm()
        return render_template('login.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # 로그인 폼 생성
    if form.validate_on_submit():  # 유효성 검사
        userid = form.data.get('userid')
        fcuser = Fcuser.query.filter_by(userid=userid).first()
        if fcuser and fcuser.password == form.data.get('password'):
            login_user(fcuser)
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', form=form, error='Invalid credentials')
    return render_template('login.html', form=form)
    
@main.route('/logout',methods=['GET'])
def logout():
    logout_user()
    return redirect('/')

@main.route('/register', methods=['GET','POST'])  #겟, 포스트 메소드 둘다 사용
@login_required
def register():   #get 요청 단순히 페이지 표시 post요청 회원가입-등록을 눌렀을때 정보 가져오는것
    form = RegisterForm()
    if form.validate_on_submit(): # POST검사의 유효성검사가 정상적으로 되었는지 확인할 수 있다. 입력 안한것들이 있는지 확인됨.
        #비밀번호 = 비밀번호 확인 -> EqulaTo
    
        fcuser = Fcuser()  #models.py에 있는 Fcuser 
        fcuser.userid = form.data.get('userid')
        fcuser.username = form.data.get('username')
        fcuser.password = form.data.get('password')
            
        print(fcuser.userid,fcuser.password)  #회원가입 요청시 콘솔창에 ID만 출력 (확인용, 딱히 필요없음)
        db.session.add(fcuser)  # id, name 변수에 넣은 회원정보 DB에 저장
        db.session.commit()  #커밋
        
        flash("가입완료! 로그인해주세요","success")  #플래시 메시지
        return redirect(url_for('main.login'))  # Redirect to the login page after successful signup
        # return "가입완료"
    return render_template('register.html', form=form)

@main.route('/get_settings', methods=['GET'])
@login_required
def get_settings():
    try:
        with open('settings.json', 'r', encoding='utf-8') as file:
            settings = json.load(file)
        return jsonify(settings)
    except FileNotFoundError:
        return jsonify({"error": "Settings file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/save_settings', methods=['POST'])
@login_required
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
    except SuccessException as e:
        return jsonify({"message": str(e)}), 200

@main.route('/get_comments', methods=['GET'])
@login_required
def get_comments():
    try:
        comments, cnt = analyzer.get_comments()
        return jsonify({"comments": comments, "cnt": cnt})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

@main.route('/overdue_comments', methods=['POST'])
@login_required
def overdue_comments():
    try:
        data = request.json
        # comments, _ = analyzer.get_comments()
        end_date = data['end_date']
        comments_remove_overdue, comments_overdue, cnt_overdue, cnt_not_overdue = analyzer.overdue_comments(end_date)
        return jsonify({
            "comments_remove_overdue": comments_remove_overdue,
            "comments_overdue": comments_overdue,
            "cnt_overdue": cnt_overdue,
            "cnt_not_overdue": cnt_not_overdue
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/find_email', methods=['POST'])
@login_required
def find_email():
    data = request.json
    comments_remove_overdue = data['comments_remove_overdue']
    comments_emails, cnt_email = analyzer.find_email()
    return jsonify({
        "comments_emails": comments_emails,
        "cnt_email": cnt_email
    })

@main.route('/find_duplicate_comments', methods=['POST'])
@login_required
def find_duplicate_comments():
    data = request.json
    comments_emails = data['comments_emails']
    comments_remove_duplicate, duplicate_emails, cnt_duplicate, cnt_not_duplicate = analyzer.find_duplicate_comments()
    return jsonify({
        "comments_remove_duplicate": comments_remove_duplicate,
        "duplicate_emails": duplicate_emails,
        "cnt_duplicate": cnt_duplicate,
        "cnt_not_duplicate": cnt_not_duplicate
    })

@main.route('/random_picker', methods=['POST'])
@login_required
def random_picker():
    try:
        data = request.json
        comments_remove_duplicate = data['comments_remove_duplicate']
        pick_number = data['pick_number']
        random_emails = analyzer.random_picker( pick_number)
        return jsonify({"random_emails": random_emails})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@main.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.html'):
        filename = "comments.html" # change filename to comments.html
        file.save(os.path.join('uploads', filename))
        analyzer.html_name = filename
        return jsonify({"message": "성공적으로 파일을 업로드했습니다."})
    else:
        return jsonify({"error": "Invalid file type"}), 400

@main.route('/save_comments', methods=['POST'])
@login_required
def save_comments():
    try:
        data = request.json
        comments = data['comments']
        filename = "comments"
        filepath = analyzer.save_data(comments, filename)
        return jsonify({"message": "Comments saved successfully", "filepath": url_for('static', filename=filepath, _external=True)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/all_in_one', methods=['POST'])
@login_required
def all_in_one():
    try:
        data = request.json
        end_date = data['end_date']
        random_emails = analyzer.all_in_one(end_date)
        return jsonify({"random_emails": random_emails})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/download_file/<path:filename>', methods=['GET'])
@login_required
def download_file(filename):
    try:
        return send_from_directory('data', filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@main.route('/exclude_comments', methods=['POST'])
@login_required
def exclude_comments():
    try:
        data = request.json
        comments_to_exclude = data['comments']
        analyzer.exclude_comments(comments_to_exclude)
        return jsonify({"message": "선택된 댓글이 성공적으로 제외되었습니다.", "updated_comments": analyzer.comments})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    main.run(debug=True)