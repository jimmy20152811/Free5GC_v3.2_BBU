from flask import Flask, jsonify, request, redirect, url_for
from flask_cors import cross_origin
from flask_jwt import JWT, jwt_required, current_identity
import pymysql
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# 資料庫連接資訊
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'rtlab111',
    'database': 'db_1',
}

# 創建 MySQL 連接
connection = pymysql.connect(**db_config)

# 創建游標
cursor = connection.cursor()

# 定義使用者類別，用於 JWT
class User:
    def __init__(self, id, s_email, access_level):
        self.id = id
        self.s_email = s_email
        self.access_level = access_level

# 用於 JWT 的回調函式
def authenticate(s_email, s_password):
    query = "SELECT * FROM table_sign_up WHERE s_email = %s AND s_password = %s"
    cursor.execute(query, (s_email, s_password))
    user = cursor.fetchone()

    if user:
        return User(id=user[0], s_email=user[2], access_level=user[-1])

# 用於生成 JWT 的回調函式
def identity(payload):
    user_id = payload['identity']
    query = "SELECT * FROM table_sign_up WHERE id = %s"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()

    if user:
        return User(id=user[0], s_email=user[2], access_level=user[-1])

# 在 Flask 中啟用 JWT
jwt = JWT(app, authenticate, identity)

# Google OAuth 資訊
GOOGLE_CLIENT_ID = 'your-client-id'
GOOGLE_CLIENT_SECRET = 'your-client-secret'
GOOGLE_REDIRECT_URI = 'your-redirect-uri'
GOOGLE_AUTHORIZATION_BASE_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'

# 註冊的路由，支援一般註冊和使用 Google 帳戶註冊
@app.route('/user/signup', methods=['POST'])
@cross_origin()
def sign_up():
    try:
        json_data = request.get_json()

        # 檢查是否包含所需的標題
        required_titles = ['s_name', 's_email', 's_password', 's_password_confirmation', 's_phone']

        # 檢查是否有任何可插入的標題為空
        if any(title not in json_data or not json_data[title].strip() for title in required_titles):
            return jsonify({'Error': 'have some parameter null'}), 403

        # 取得 'access_level' 的值，如果不存在，預設值為 0
        access_level = json_data.get('access_level', 0)

        # 準備用於插入的標題和值
        insert_titles = required_titles + ['access_level']
        insert_values = [json_data[title] for title in required_titles] + [access_level]

        # 檢查 's_password' 和 's_password_confirmation' 是否相同
        if 's_password' in json_data and 's_password_confirmation' in json_data:
            if json_data['s_password'] != json_data['s_password_confirmation']:
                return jsonify({'Error': 'need identical password'}), 401

        # 檢查 's_email' 是否已經存在於表格中
        check_email_query = "SELECT COUNT(*) FROM table_sign_up WHERE s_email = %s"
        cursor.execute(check_email_query, (json_data['s_email'],))
        email_exists = cursor.fetchone()[0]

        if email_exists:
            return jsonify({'Error': 'email already registers'}), 402

        # 插入資料到 MySQL 表格
        insert_query = f"INSERT INTO table_sign_up ({', '.join(insert_titles)}) VALUES ({', '.join(['%s']*len(insert_titles))})"
        cursor.execute(insert_query, insert_values)
        connection.commit()

        # 加入 print 語句以記錄成功接收並插入資料
        print(f"Received JSON: {json_data}")

        return jsonify({'message': 'JSON received successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Google 登入路由，導向 Google 登入頁面
@app.route('/user/google-login')
@cross_origin()
def google_login():
    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI)
    authorization_url, state = google.authorization_url(GOOGLE_AUTHORIZATION_BASE_URL)
    return redirect(authorization_url)

# Google 登入回調路由
@app.route('/user/google-callback')
@cross_origin()
def google_callback():
    try:
        google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI)
        token = google.fetch_token(GOOGLE_TOKEN_URL, authorization_response=request.url)
        user_info = google.get(GOOGLE_USERINFO_URL).json()

        # 在這裡處理 Google 登入成功後的邏輯
        # 你可能需要在資料庫中檢查使用者是否存在，如果不存在就創建一個新的使用者

        return jsonify({'message': 'Google login successful', 'user_info': user_info}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 登入的路由，支援一般登入和使用 Google 帳戶登入
@app.route('/user/login', methods=['POST'])
@cross_origin()
def login():
    try:
        json_data = request.get_json()

        # 使用一般帳戶登入
        if 's_email' in json_data and 's_password' in json_data:
            user = authenticate(json_data['s_email'], json_data['s_password'])

            if user:
                # 生成 JWT
                access_token = jwt.jwt_encode_callback(user)
                return jsonify({'access_token': access_token.decode('utf-8'), 'user_info': {'s_email': user.s_email, 'access_level': user.access_level}}), 200
            else:
                return jsonify({'Error': 'Invalid credentials'}), 401

        # 使用 Google 帳戶登入
        elif 'google_token' in json_data:
            # 在這裡處理使用 Google 帳戶登入的邏輯
            # 你可能需要在資料庫中檢查使用者是否存在，如果不存在就創建一個新的使用者

            return jsonify({'message': 'Google login successful'}), 200

        else:
            return jsonify({'Error': 'Invalid login request'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(host='192.168.0.2', port=5000, debug=True)
