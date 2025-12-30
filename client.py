import socket
import threading
import tkinter as tk
import winsound
import hashlib
import random
from datetime import datetime
from tkinter import scrolledtext, messagebox

HOST = "127.0.0.1"
PORT = 12345

client = None
username = None
root = None
current_window = None

# ===== AVATAR ỔN ĐỊNH =====
AVATARS = ["😄", "😎", "🤖", "🐱", "🐶", "🔥", "🌟", "🍀"]

def get_avatar_by_username(name):
    md5 = hashlib.md5(name.encode("utf-8")).hexdigest()
    return AVATARS[int(md5, 16) % len(AVATARS)]

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

# ===== EMOJI BAY (THÊM MỚI – KHÔNG ẢNH HƯỞNG CODE CŨ) =====
FLY_EMOJI_KEYWORDS = ["❤️", "🔥", "👍", "😄", "😢", "😃", "😉"]

def fly_emoji(emoji):
    lbl = tk.Label(root, text=emoji, font=("Arial", 24))
    lbl.place(x=random.randint(30, 400), y=520)

    def animate(y):
        if y < 0:
            lbl.destroy()
            return
        lbl.place(y=y)
        root.after(30, lambda: animate(y - 12))

    animate(520)

def check_fly_effect(text):
    for emo in FLY_EMOJI_KEYWORDS:
        if emo in text:
            fly_emoji(emo)

# ================= SERVER =================
def connect_to_server():
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        return client.recv(1024).decode().strip() == "READY"
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
            status.config(text="Nhập đầy đủ thông tin")
            return
        client.send(f"REGISTER|{u}|{p}".encode())
        if client.recv(1024).decode() == "SUCCESS":
            current_window.after(500, login_screen)
        else:
            status.config(text="Tài khoản đã tồn tại")

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

    chat_box.tag_config("name_me", justify="right", font=("Arial", 11, "bold"), foreground="#0084ff")
    chat_box.tag_config("name_other", justify="left", font=("Arial", 11, "bold"))
    chat_box.tag_config("msg_me", justify="right")
    chat_box.tag_config("msg_other", justify="left")
    chat_box.tag_config("time_me", justify="right", font=("Arial", 8), foreground="gray")
    chat_box.tag_config("time_other", justify="left", font=("Arial", 8), foreground="gray")

    my_avatar = get_avatar_by_username(username)

    def send_msg(event=None):
        msg = entry.get().strip()
        if not msg:
            return

        msg = replace_emoji(msg)
        check_fly_effect(msg)   # 🔥 THÊM EMOJI BAY

        client.send(f"{username}: {msg}\n".encode())
        winsound.MessageBeep()

        t = datetime.now().strftime("%H:%M")

        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"{my_avatar} {username}\n", "name_me")
        chat_box.insert(tk.END, msg + "\n", "msg_me")
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
                    sender, content = line.split(": ", 1)
                    if sender == username:
                        continue

                    content = replace_emoji(content)
                    check_fly_effect(content)   # 🔥 EMOJI BAY KHI NHẬN

                    avatar = get_avatar_by_username(sender)
                    t = datetime.now().strftime("%H:%M")

                    chat_box.config(state=tk.NORMAL)
                    chat_box.insert(tk.END, f"{avatar} {sender}\n", "name_other")
                    chat_box.insert(tk.END, content + "\n", "msg_other")
                    chat_box.insert(tk.END, t + "\n\n", "time_other")
                    chat_box.config(state=tk.DISABLED)
                    chat_box.see(tk.END)

    entry.bind("<Return>", send_msg)
    send_btn.config(command=send_msg)
    threading.Thread(target=receive, daemon=True).start()
    root.mainloop()

# ================= START =================
login_screen()
