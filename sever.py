import socket
import threading
import json
import hashlib
import os
import tkinter as tk
from tkinter import scrolledtext

HOST = "0.0.0.0"    # Lắng nghe trên mọi interface (có thể truy cập từ mạng ngoài)  
PORT = 12345        # Cổng server

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

clients = []  # list of tuples [(socket, username)]

# Tạo GUI admin
admin_root = tk.Tk()
admin_root.title("Server Admin Dashboard")
admin_root.geometry("800x600")
#log_box
log_box = scrolledtext.ScrolledText(admin_root, state=tk.DISABLED)
log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
#online_label
online_label = tk.Label(admin_root, text="Online: 0 người", fg="green", font=("Arial", 12))
online_label.pack(anchor="w", padx=10)

def admin_log(message, color="black"):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, message + "\n", color)
    log_box.config(state=tk.DISABLED)
    log_box.see(tk.END)

def update_online():
    online_list = ", ".join([name for _, name in clients])
    count = len(clients)
    online_label.config(text=f"Online ({count}): {online_list or 'Trống'}")
    admin_root.after(1000, update_online)  # cập nhật 1s một lần

# Tag màu cho log
log_box.tag_config("green", foreground="green")
log_box.tag_config("red", foreground="red")
log_box.tag_config("blue", foreground="blue")
log_box.tag_config("magenta", foreground="magenta")

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
            admin_log(f"{name} đã rời khỏi phòng chat.")
            update_online()  # Update ngay khi leave
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
        #Xử lý đăng ký
        if action == "REGISTER":
            if username in accounts:
                client_sock.send("TAKEN".encode("utf-8"))
                return
            else:
                accounts[username] = hash_password(password)
                save_accounts()
                client_sock.send("SUCCESS".encode("utf-8"))
                admin_log(f"Tài khoản mới tạo: {username} từ {addr}")
                return  # Không vào chat, client sẽ reconnect và login
        #Xử lý đăng nhập
        elif action == "LOGIN":
            if username in accounts and accounts[username] == hash_password(password):
                client_sock.send("SUCCESS".encode("utf-8"))
                authenticated = True
            else:
                client_sock.send("FAIL".encode("utf-8"))
                admin_log(f"Đăng nhập thất bại: {username} từ {addr}", "yellow")
                return

        # Chỉ vào đây nếu LOGIN thành công
        if authenticated:
            clients.append((client_sock, username)) #Thêm vào ds Client hoạt động
            admin_log(f"{username} ({addr}) đã đăng nhập và tham gia chat")
            broadcast(f"{username} đã tham gia phòng chat!\n")
            update_online()  # Update ngay khi join

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
        admin_log(f"Lỗi với client {addr}: {e}")
    finally:
        remove_client(client_sock)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    admin_log(f"Server chạy trên port {PORT}")
    admin_log("Chờ client đăng ký/đăng nhập...")

    while True: #-> Chờ kết nối
        client_sock, addr = server.accept()
        admin_log(f"Kết nối từ {addr}")
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    # Chạy server loop trong thread daemon (nền, không block GUI)
    threading.Thread(target=main, daemon=True).start()

    # Sau đó chạy GUI chính (foreground)
    update_online()  # Bắt đầu cập nhật danh sách online
    admin_log("=== SERVER ADMIN DASHBOARD KHỞI ĐỘNG ===", "green")
    admin_root.mainloop()  # Đây là vòng lặp chính giữ cửa sổ GUI sống (Chạy GUIs)