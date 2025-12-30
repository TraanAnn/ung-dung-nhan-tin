import socket
import threading
import tkinter as tk
import random
import winsound
import hashlib
from datetime import datetime
from tkinter import scrolledtext, messagebox, simpledialog

HOST = "127.0.0.1"
PORT = 12345

root = None
client = None
current_window = None
username = None

# ===== AVATAR (ỔN ĐỊNH – KHÔNG BAO GIỜ LỆCH) =====
AVATARS = ["😄", "😎", "🤖", "🐱", "🐶", "🔥", "🌟", "🍀"]

def get_avatar_by_username(name):
    md5 = hashlib.md5(name.encode("utf-8")).hexdigest()
    index = int(md5, 16) % len(AVATARS)
    return AVATARS[index]

# ===== EMOJI =====
EMOJI_MAP = {
    ":)": "😄",
    ":(": "😢",
    ":D": "😃",
    ";)": "😉",
    ":heart:": "❤️",
    ":thumbsup:": "👍",
    ":fire:": "🔥"
}

def replace_emoji(text):
    for k, v in EMOJI_MAP.items():
        text = text.replace(k, v)
    return text

def connect_to_server():
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        signal = client.recv(1024).decode().strip()
        return signal == "READY"
    except:
        messagebox.showerror("Lỗi", "Không thể kết nối server")
        return False

# ================= ĐĂNG KÝ =================
def register_screen():
    global current_window
    if current_window:
        current_window.destroy()
    if not connect_to_server():
        return

    current_window = tk.Tk()
    current_window.title("Đăng ký tài khoản")
    current_window.geometry("600x600")
    current_window.resizable(False, False)

    tk.Label(current_window, text="ĐĂNG KÝ",
             font=("Arial", 24, "bold")).pack(pady=40)

    frame = tk.Frame(current_window)
    frame.pack(pady=20)

    tk.Label(frame, text="Tên tài khoản:").pack(anchor="w")
    user_entry = tk.Entry(frame, width=30)
    user_entry.pack(pady=10)

    tk.Label(frame, text="Mật khẩu:").pack(anchor="w")
    pass_entry = tk.Entry(frame, width=30, show="*")
    pass_entry.pack(pady=10)

    status = tk.Label(current_window, fg="red")
    status.pack()

    def do_register():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()
        if not u or not p:
            status.config(text="Nhập đầy đủ")
            return
        client.send(f"REGISTER|{u}|{p}".encode())
        res = client.recv(1024).decode()
        if res == "SUCCESS":
            current_window.after(500, login_screen)
        else:
            status.config(text="Tài khoản tồn tại")

    tk.Button(current_window, text="Đăng ký",
              command=do_register, width=20).pack(pady=20)
    tk.Button(current_window, text="← Quay lại",
              command=login_screen).pack()

    current_window.mainloop()

# ================= ĐĂNG NHẬP =================
def login_screen():
    global current_window
    if current_window:
        current_window.destroy()
    if not connect_to_server():
        return

    current_window = tk.Tk()
    current_window.title("Chat App - Đăng nhập")
    current_window.geometry("600x600")
    current_window.resizable(False, False)

    tk.Label(current_window, text="CHAT APP",
             font=("Arial", 28, "bold")).pack(pady=50)

    frame = tk.Frame(current_window)
    frame.pack(pady=20)

    tk.Label(frame, text="Tên tài khoản:").pack(anchor="w")
    user_entry = tk.Entry(frame, width=30)
    user_entry.pack(pady=10)

    tk.Label(frame, text="Mật khẩu:").pack(anchor="w")
    pass_entry = tk.Entry(frame, width=30, show="*")
    pass_entry.pack(pady=10)

    status = tk.Label(current_window, fg="red")
    status.pack()

    def do_login():
        global username
        username = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        client.send(f"LOGIN|{username}|{pwd}".encode())
        if client.recv(1024).decode() == "SUCCESS":
            current_window.after(500, open_chat)
        else:
            status.config(text="Sai thông tin")

    tk.Button(current_window, text="Đăng nhập",
              command=do_login, width=20).pack(pady=20)
    tk.Button(current_window, text="Chưa có tài khoản? Đăng ký ngay",
              command=register_screen, fg="blue", bd=0).pack()

    current_window.mainloop()

# ================= CHAT =================
def open_chat():
    global root, current_window
    if current_window:
        current_window.destroy()

    root = tk.Tk()
    root.title(f"Chat App - {username}")
    root.geometry("600x700")

    chat_box = scrolledtext.ScrolledText(
        root, state=tk.DISABLED, font=("Arial", 11))
    chat_box.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

    entry = tk.Entry(input_frame)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    send_btn = tk.Button(input_frame, text="Gửi", width=10)
    send_btn.pack(side=tk.RIGHT)

    chat_box.tag_config("me", justify="right", foreground="#0084ff")
    chat_box.tag_config("other", justify="left")
    chat_box.tag_config("time_me", justify="right", font=("Arial", 8))
    chat_box.tag_config("time_other", justify="left", font=("Arial", 8))

    my_avatar = get_avatar_by_username(username)

    def send_msg(event=None):
        msg = entry.get().strip()
        if not msg:
            return
        msg = replace_emoji(msg)
        client.send(f"{username}: {msg}\n".encode())
        winsound.MessageBeep()

        t = datetime.now().strftime("%H:%M")
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"{my_avatar} {username} : {msg}\n", "me")
        chat_box.insert(tk.END, t + "\n\n", "time_me")
        chat_box.config(state=tk.DISABLED)
        chat_box.see(tk.END)
        entry.delete(0, tk.END)

    def receive():
        buf = ""
        while True:
            data = client.recv(1024)
            if not data:
                break
            buf += data.decode()
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if ": " in line:
                    s, c = line.split(": ", 1)
                    if s == username:
                        continue
                    av = get_avatar_by_username(s)
                    t = datetime.now().strftime("%H:%M")
                    chat_box.config(state=tk.NORMAL)
                    chat_box.insert(tk.END, f"{av} {s} : {c}\n", "other")
                    chat_box.insert(tk.END, t + "\n\n", "time_other")
                    chat_box.config(state=tk.DISABLED)
                    chat_box.see(tk.END)

    entry.bind("<Return>", send_msg)
    send_btn.config(command=send_msg)
    threading.Thread(target=receive, daemon=True).start()
    root.mainloop()

# ================= START =================
login_screen()
