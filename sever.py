import socket
import threading
import json
import hashlib
import os

HOST = "0.0.0.0"
PORT = 12345

ACCOUNTS_FILE = "accounts.json"

# Tải tài khoản
if os.path.exists(ACCOUNTS_FILE):
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        accounts = json.load(f)
else:
    accounts = {}

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=4)

clients = []  # [(socket, username)]

def broadcast(message, sender_sock=None):
    for sock, _ in clients:
        if sock == sender_sock:
            continue
        try:
            sock.send(message.encode("utf-8"))
        except:
            remove_client(sock)

def remove_client(sock):
    for i in range(len(clients)):
        if clients[i][0] == sock:
            name = clients[i][1]
            del clients[i]
            broadcast(f"{name} đã rời khỏi phòng chat.\n")
            print(f"{name} đã rời khỏi phòng chat.")
            break
    try:
        sock.close()
    except:
        pass

def handle_client(client_sock, addr):
    try:
        client_sock.send("READY".encode("utf-8"))

        data = client_sock.recv(4096).decode("utf-8").strip()
        if not data:
            return

        parts = data.split("|")
        if len(parts) != 3:
            return

        action, username, password = parts
        authenticated = False

        if action == "REGISTER":
            if username in accounts:
                client_sock.send("TAKEN".encode("utf-8"))
            else:
                accounts[username] = hash_password(password)
                save_accounts()
                client_sock.send("SUCCESS".encode("utf-8"))
                print(f"Tài khoản mới tạo: {username} từ {addr}")
                return  # Không vào chat, client sẽ reconnect và login

        elif action == "LOGIN":
            if username in accounts and accounts[username] == hash_password(password):
                client_sock.send("SUCCESS".encode("utf-8"))
                authenticated = True
            else:
                client_sock.send("FAIL".encode("utf-8"))
                return

        # Chỉ vào đây nếu LOGIN thành công
        if authenticated:
            clients.append((client_sock, username))
            print(f"{username} ({addr}) đã đăng nhập và tham gia chat")
            broadcast(f"{username} đã tham gia phòng chat!\n")

            # Vòng lặp chat + typing
            while True:
                try:
                    msg = client_sock.recv(1024)
                    if not msg:
                        break
                    data = msg.decode("utf-8")
                    lines = data.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line:
                            broadcast(line + "\n")
                except:
                    break

    except Exception as e:
        print(f"Lỗi với client {addr}: {e}")
    finally:
        remove_client(client_sock)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server chạy trên port {PORT}")
    print("Chờ client đăng ký/đăng nhập...")

    while True:
        client_sock, addr = server.accept()
        print(f"Kết nối từ {addr}")
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    main()