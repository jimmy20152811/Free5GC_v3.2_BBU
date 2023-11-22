from flask import Flask, jsonify, request, redirect, url_for
import pymysql
from flask_cors import cross_origin
from flask_jwt import JWT, jwt_required, current_identity
from requests_oauthlib import OAuth2Session
import secrets
import os
import schedule
import time
from flask_socketio import SocketIO
from threading import Thread

app = Flask(__name__)
# 初始化 Socket.IO
socketio = SocketIO(app)
app.config['SECRET_KEY'] = secrets.token_hex(16)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# MySQL 連接資訊
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'rtlab111',
    'database': 'db_1',
    #'port': 3306
}

# 處理 404 錯誤
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

# 創建 MySQL 連接
connection = pymysql.connect(**db_config)

# 創建游標
cursor = connection.cursor()

# 定義使用者類別，用於 JWT
class User:
    def __init__(self, id, s_name, s_email, s_phone, access_level):
        self.id = id
        self.s_name = s_name
        self.s_email = s_email
        self.s_phone = s_phone
        self.access_level = access_level

# 用於 JWT 的回調函式
def authenticate(s_name, s_password):
    query = "SELECT * FROM table_sign_up WHERE s_name = %s AND s_password = %s"
    cursor.execute(query, (s_name, s_password))
    user = cursor.fetchone()

    if user:
        return User(id=user[0], s_name=user[1], s_email=user[2], s_phone=user[5], access_level=user[-1])

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
GOOGLE_CLIENT_ID = '92303118686-evca8stap1l4t512m5nobbgaog7pllvk.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_REDIRECT_URI = 'https://a7da-140-118-121-93.ngrok-free.app/user/google-callback'
GOOGLE_AUTHORIZATION_BASE_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'

# Google 登入路由，導向 Google 登入頁面
@app.route('/user/google-login')
@cross_origin()
def google_login():
    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI, scope=['openid', 'email', 'profile'])
    authorization_url, state = google.authorization_url(GOOGLE_AUTHORIZATION_BASE_URL)
    return redirect(authorization_url)
# 這裡沒有加上手機，因為不包含要求這個功能

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
        existing_user_query = "SELECT * FROM table_sign_up WHERE s_email = %s"
        cursor.execute(existing_user_query, (user_info['email'],))
        existing_user = cursor.fetchone()

        if existing_user:
            # 使用現有使用者的資訊
            user = User(id=existing_user[0], s_name=existing_user[1], s_email=existing_user[2], s_phone=existing_user[5], access_level=existing_user[-1])
        else:
            # 創建新的使用者
            insert_user_query = "INSERT INTO table_sign_up (s_name, s_email, access_level) VALUES (%s, %s, %s)"
            cursor.execute(insert_user_query, (user_info['name'], user_info['email'], 0))  # 這裡假設使用者的預設權限是 0
            connection.commit()
            
            # 取得新使用者的資訊
            cursor.execute(existing_user_query, (user_info['email'],))
            new_user = cursor.fetchone()
            user = User(id=new_user[0], s_name=new_user[1], s_email=new_user[2], s_phone=new_user[5], access_level=new_user[-1])

        # 在這裡執行重定向
        return jsonify({'message': 'Google login successful', 'user_info': {'s_name': user.s_name, 's_email': user.s_email, 's_phone': user.s_phone, 'access_level': user.access_level}}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/user/google-userinfo', methods=['GET'])
@cross_origin()
def google_userinfo():
    try:
        google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI)
        # token = google.fetch_token(GOOGLE_TOKEN_URL, authorization_response=request.url)
        user_info = google.get(GOOGLE_USERINFO_URL).json()

        # 在這裡處理 Google 登入成功後的邏輯
        # 你可能需要在資料庫中檢查使用者是否存在，如果不存在就創建一個新的使用者
        existing_user_query = "SELECT * FROM table_sign_up WHERE s_email = %s"
        cursor.execute(existing_user_query, (user_info['email'],))
        existing_user = cursor.fetchone()

        if existing_user:
            # 使用現有使用者的資訊
            user = User(id=existing_user[0], s_name=existing_user[1], s_email=existing_user[2], s_phone=existing_user[5], access_level=existing_user[-1])
        else:
            # 創建新的使用者
            insert_user_query = "INSERT INTO table_sign_up (s_name, s_email, access_level) VALUES (%s, %s, %s)"
            cursor.execute(insert_user_query, (user_info['name'], user_info['email'], 0))  # 這裡假設使用者的預設權限是 0
            connection.commit()
            
            # 取得新使用者的資訊
            cursor.execute(existing_user_query, (user_info['email'],))
            new_user = cursor.fetchone()
            user = User(id=new_user[0], s_name=new_user[1], s_email=new_user[2], s_phone=new_user[5], access_level=new_user[-1])

        # 在這裡執行重定向
        return jsonify({'message': 'Google login successful', 'user_info': {'s_name': user.s_name, 's_email': user.s_email, 's_phone': user.s_phone, 'access_level': user.access_level}}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 登入的路由，支援一般登入和使用 Google 帳戶登入
@app.route('/user/login', methods=['POST'])
@cross_origin()
def login():
    try:
        json_data = request.get_json()
        
         # 檢查是否包含所需的標題
        required_titles = ['s_name', 's_password']

        # 檢查是否有任何可插入的標題為空
        if any(title not in json_data or not json_data[title].strip() for title in required_titles):
            return jsonify({'Error': 'Missing required parameters'}), 400

        # 使用一般帳戶登入
        if 's_name' in json_data and 's_password' in json_data:
            user = authenticate(json_data['s_name'], json_data['s_password'])

            if user:
                # 生成 JWT
                access_token = jwt.jwt_encode_callback(user)
                # 返回使用者所有資訊，不包括密碼
                return jsonify({'message': 'Login successful', 'user_info': {'s_name': user.s_name, 's_email': user.s_email, 's_phone': user.s_phone, 'access_level': user.access_level}, 'access_token': access_token.decode('utf-8')}), 200
            else:
                return jsonify({'Error': 'Invalid credentials'}), 400
            
        else:
            return jsonify({'error'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
    
    
# 新的端點，用於接收 POST 請求並添加新的 user
@app.route('/user/signup', methods=['POST'])
@cross_origin()  # 使用 @cross_origin 裝飾器啟用 CORS
def sign_up():
    try:
        json_data = request.get_json()

        # 檢查是否包含所需的標題
        required_titles = ['s_name', 's_email', 's_password', 's_password_confirmation', 's_phone']

        # 檢查是否有任何可插入的標題為空
        if any(title not in json_data or not json_data[title].strip() for title in required_titles):
            return jsonify({'Error': 'have some parameter null'}), 403
        
        # 取得 'access_level' 的值，如果不存在，預設值為 0
        access_level = request.headers.get('Authorization', 0)

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

# 新的端點，用於接收 POST 請求並添加新的 log
@app.route('/nfs/resource', methods=['POST'])
@cross_origin()  # 使用 @cross_origin 裝飾器啟用 CORS
def add_log():
    
    try:
        json_data = request.get_json()

        # 檢查是否包含所需的標題
        required_titles = ['dt_infotime', 's_attemp', 's_cpu', 's_disk', 's_diskin', 's_diskout',
                            's_error', 's_load', 's_loss', 's_memory', 's_nf', 's_size',
                            's_system', 's_traffic', 's_transfer']

        # 準備用於插入的標題和值
        insert_titles = []
        insert_values = []

        for title in required_titles:
            if title in json_data:
                insert_titles.append(title)
                insert_values.append(json_data[title])
            elif title not in json_data:
                return jsonify({'error': f'Missing title: {title}'}), 404

        # 檢查是否有任何可插入的標題
        #if not insert_titles:
        #    return jsonify({'error': 'No valid data to insert'}), 400

        # 插入資料到 MySQL 表格
        insert_query = f"INSERT INTO table_2 ({', '.join(insert_titles)}) VALUES ({', '.join(['%s']*len(insert_titles))})"
        cursor.execute(insert_query, insert_values)
        connection.commit()

        # 加入 print 語句以記錄成功接收並插入資料
        print(f"Received JSON: {json_data}")

        return jsonify({'message': 'JSON received successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 404

# 新的端點，用於接收 GET 請求
@app.route('/nfs/resource', methods=['GET'])
@cross_origin()  # 使用 @cross_origin 裝飾器啟用 CORS
def get_s_nf():
    try:
        # 從 GET 參數中獲取 s_nf 的值
        s_nf_value = request.args.get('s_nf')

        # 檢查是否有 s_nf 參數
        if s_nf_value is None:
            return jsonify({'error': 'Missing s_nf parameter'}), 404

        # 執行 SELECT 查詢，找到最後一筆 s_nf=amf 的資料按照 id 降序排序
        select_query = "SELECT * FROM table_2 WHERE s_nf = %s ORDER BY id DESC LIMIT 1"
        cursor.execute(select_query, (s_nf_value,))

        # 獲取查詢結果
        result = cursor.fetchone()

        # 將結果轉換為 JSON 格式並返回
        data = {"dt_infotime": result[0], "s_attemp": result[1], "s_cpu": result[2], "s_disk": result[3], "s_diskin": result[4], "s_diskout": result[5]
             , "s_error": result[6], "s_load": result[7], "s_loss": result[8], "s_memory": result[9] #, "s_nf": result[10]
               , "s_size": result[11], "s_system": result[12], "s_traffic": result[13], "s_transfer": result[14]}  # 根據實際情況修改列名
        return jsonify({'data': data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 404
    
    
def calculate_average_cpu_usage():
    # 執行 SQL 查詢以獲取 s_cpu 數據
    select_query = "SELECT s_cpu FROM table_2 WHERE s_nf = 'amf'"
    cursor.execute(select_query)

    # 獲取查詢結果
    cpu_data = cursor.fetchall()

    # 轉換 s_cpu 的數據為數字並計算總和
    total_cpu = sum(float(data[0]) for data in cpu_data)

    # 計算 s_cpu 的平均值
    if cpu_data:
        average_cpu = total_cpu / len(cpu_data)
        return average_cpu
    else:
        return 0  # 或者返回其他預設值



# 定義 Socket.IO 事件處理程序（用於向前端發送警告）
@socketio.on('alert')
def handle_alert(alert_data):
    print('Received alert data:', alert_data)
    # 在這裡可以向前端發送警告

def job():
    # 計算平均 s_cpu 使用率
    average_cpu = calculate_average_cpu_usage()

    # 檢查是否超過 90%
    if average_cpu > 90:
        # 發送警告到前端
        alert_data = {'message': 'High CPU Usage', 'average_cpu': average_cpu}
        socketio.emit('alert', alert_data)

# 定義定時任務，每分鐘執行一次
schedule.every(1).minutes.do(job)

def run_flask_app():
    # 啟動 Socket.IO
    socketio.run(app, host='192.168.0.2', port=5000, debug=True, use_reloader=False)

# 在一個新的執行緒中運行 Flask 應用程式
flask_thread = Thread(target=run_flask_app)
flask_thread.start()

# 在主執行緒中執行定時任務
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        break  # 中斷程式

# 等待 Flask 應用程式執行緒完成
flask_thread.join()