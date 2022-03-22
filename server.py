import socket
import threading
import sqlite3

clientList = []

# 쓰레드에서 실행되는 코드입니다.
# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다.
def threaded(clientSocket, addr):
    global clientList
    print('Connected by :', addr[0], ':', addr[1])
    try:
        conn = sqlite3.connect("user.db")
        cur = conn.cursor()

        while True:
            data = clientSocket.recv(1024)
            print(data.decode())
            msgList = data.decode().split('/')
            if msgList[0] == 'Chat':
                if msgList[1] == 'Send':
                    print('receive message: ' + msgList[2])
                    clientSocket.send(('Chat/Send/' + msgList[2]).encode())
            elif msgList[0] == 'Login':
                query = "SELECT * FROM user WHERE id='%s'" % msgList[1]
                cur.execute(query)
                result = []
                for data in cur.fetchone():
                    result.append(data)
                if msgList[1] == result[0]:
                    if msgList[2] == result[1]:
                        print('add friendlist: ' + msgList[1])
                        clientList.append((clientSocket, msgList[1]))
                        print(clientList)
                        clientSocket.send('Login/Success'.encode())
                    else:
                        clientSocket.send('Login/Error/비밀번호가 맞지 않습니다.'.encode())
                else:
                    clientSocket.send('Login/Error/아이디가 존재하지 않습니다.'.encode())
            elif msgList[0] == 'FriendList':
                if msgList[1] == 'Get':
                    print('friendList get: ' + str(clientList))
                    idList = []
                    for i in clientList:
                        idList.append(i[1])
                    clientSocket.send(('FriendList/Receive/' + str(idList)).encode())

    except ConnectionResetError as e:
        print('Disconnected by ' + addr[0], ':', addr[1])
        clientSocket.close()

HOST = '127.0.0.1'
PORT = 6666

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
serverSocket.listen()

print('server start')

# 클라이언트가 접속하면 accept 함수에서 새로운 소켓을 리턴합니다.
# 새로운 쓰레드에서 해당 소켓을 사용하여 통신을 하게 됩니다.
while True:
    print('wait')

    clientSocket, addr = serverSocket.accept()
    print('client accpet addr = ', addr)
    t = threading.Thread(target=threaded, args=(clientSocket, addr))
    t.start()

serverSocket.close()