// socketio_client.js

const io = require('socket.io-client');
const socket = io('http://192.168.0.2:5000');

// 監聽 "alert" 事件
socket.on('alert', function (data) {
    console.log('Received alert:', data);
    // 在這裡處理接收到的警告信息
});
