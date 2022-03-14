import socket
import threading

clientList = []

# 쓰레드에서 실행되는 코드입니다.
# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다.
def threaded(clientSocket, addr):
    global clientList
    print('Connected by :', addr[0], ':', addr[1])
    try:
        while True:
            data = clientSocket.recv(1024)
            print(data.decode())
            msgList = data.decode().split('/')
            if msgList[0] == 'Chat':
                if msgList[1] == 'Send':
                    print('receive message: ' + msgList[2])
                    clientSocket.send(('Chat/Send/' + msgList[2]).decode())
            elif msgList[0] == 'FriendList':
                if msgList[1] == 'Add':
                    print('add friendlist: ' + msgList[2])
                    clientList.append((clientSocket, msgList[2]))
                    print(clientList)
                    clientSocket.send(('FriendList/Add/' + msgList[2]).decode())
            clientSocket.send(data)

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