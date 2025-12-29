import socket
import threading

HOST = "0.0.0.0"
PORT = 12345

clients = []

def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            clients.remove(client)

def handle_client(client):
    while True:
        try:
            msg = client.recv(1024)
            if not msg:
                break
            broadcast(msg)
        except:
            break

    clients.remove(client)
    client.close()
    broadcast("Một người đã rời khỏi phòng.\n".encode("utf-8"))

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Server đang chạy...")

    while True:
        client, addr = server.accept()
        print("Kết nối từ", addr)
        clients.append(client)
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

main()
