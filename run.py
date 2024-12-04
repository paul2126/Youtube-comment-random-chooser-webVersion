from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True) 
     #포트번호는 기본 5000, 개발단계에서는 debug는 True