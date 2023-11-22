# socketio_server.py
from flask import Flask
from flask_socketio import SocketIO
import schedule
import time

app = Flask(__name__)
socketio = SocketIO(app)

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

# 啟動定時任務
while True:
    schedule.run_pending()
    time.sleep(1)

if __name__ == '__main__':
    # 啟動 Socket.IO
    socketio.run(app, host='192.168.0.2', port=5000, debug=True)
