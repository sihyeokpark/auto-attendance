import socket
import threading

def send(socket):
    while True:
        message = input('>>> ')
        if message == 'quit':
            exit()
        socket.send(message.encode())

def receive(socket):
    while True:
        data = socket.recv(1024)
        print(repr(data.decode()))

# 쓰레드에서 실행되는 코드입니다.
# 접속한 클라이언트마다 새로운 쓰레드가 생성되어 통신을 하게 됩니다.
def threaded(client_socket, addr):
    print('Connected by :', addr[0], ':', addr[1])
    try:
        s = threading.Thread(target=send, args=(client_socket,))  # 여기서 , 는 왜 붙이는 걸까
        r = threading.Thread(target=receive, args=(client_socket,))
        s.start()
        r.start()

    except ConnectionResetError as e:
        print('Disconnected by ' + addr[0], ':', addr[1])
        client_socket.close()

HOST = '127.0.0.1'
PORT = 6666

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

print('server start')

# 클라이언트가 접속하면 accept 함수에서 새로운 소켓을 리턴합니다.
# 새로운 쓰레드에서 해당 소켓을 사용하여 통신을 하게 됩니다.
while True:
    print('wait')

    client_socket, addr = server_socket.accept()
    t = threading.Thread(target=threaded, args=(client_socket, addr))
    t.start()

server_socket.close()