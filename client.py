import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

HOST = "127.0.0.1"
PORT = 12345

client = None
current_window = None
username = None
is_typing = False

def connect_to_server():
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        signal = client.recv(1024).decode("utf-8").strip()
        if signal != "READY":
            messagebox.showerror("Lỗi", "Server không sẵn sàng!")
            return False
        return True
    except:
        messagebox.showerror("Lỗi", "Không thể kết nối server!")
        return False

# ====================== ĐĂNG KÝ ======================
def register_screen():
    global current_window
    if current_window:
        current_window.destroy()
    if not connect_to_server():
        return

    current_window = tk.Tk()
    current_window.title("Đăng ký tài khoản")
    current_window.geometry("350x500")
    current_window.resizable(False, False)

    tk.Label(current_window, text="ĐĂNG KÝ", font=("Arial", 24, "bold"), fg="#3498db").pack(pady=40)

    frame = tk.Frame(current_window)
    frame.pack(pady=20)

    tk.Label(frame, text="Tên tài khoản:", font=12).grid(row=0, column=0, sticky="w", pady=(0,10))
    user_entry = tk.Entry(frame, width=30, font=12)
    user_entry.grid(row=1, column=0, pady=(0,20))
    user_entry.focus()

    tk.Label(frame, text="Mật khẩu:", font=12).grid(row=2, column=0, sticky="w", pady=(0,10))
    pass_entry = tk.Entry(frame, width=30, font=12, show="*")
    pass_entry.grid(row=3, column=0, pady=(0,20))

    status = tk.Label(current_window, text="", fg="red", font=11)
    status.pack(pady=10)

    def do_register():
        uname = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        if not uname or not pwd:
            status.config(text="Vui lòng nhập đầy đủ!")
            return
        try:
            client.send(f"REGISTER|{uname}|{pwd}".encode("utf-8"))
            result = client.recv(1024).decode("utf-8").strip()
            if result == "SUCCESS":
                status.config(text="Đăng ký thành công! Đang về đăng nhập...", fg="green")
                current_window.after(1500, login_screen)
            elif result == "TAKEN":
                status.config(text="Tên tài khoản đã tồn tại!")
        except:
            status.config(text="Lỗi kết nối!")

    tk.Button(current_window, text="Đăng ký", command=do_register, bg="#3498db", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(current_window, text="← Quay lại đăng nhập", command=login_screen, bg="#95a5a6", fg="white").pack(pady=5)

    current_window.mainloop()

# ====================== ĐĂNG NHẬP ======================
def login_screen():
    global current_window
    if current_window:
        current_window.destroy()
    if not connect_to_server():
        return

    current_window = tk.Tk()
    current_window.title("Chat App - Đăng nhập")
    current_window.geometry("350x500")
    current_window.resizable(False, False)

    tk.Label(current_window, text="CHAT APP", font=("Arial", 28, "bold"), fg="#2c3e50").pack(pady=50)

    frame = tk.Frame(current_window)
    frame.pack(pady=20)

    tk.Label(frame, text="Tên tài khoản:", font=12).grid(row=0, column=0, sticky="w", pady=(0,10))
    user_entry = tk.Entry(frame, width=30, font=12)
    user_entry.grid(row=1, column=0, pady=(0,20))
    user_entry.focus()

    tk.Label(frame, text="Mật khẩu:", font=12).grid(row=2, column=0, sticky="w", pady=(0,10))
    pass_entry = tk.Entry(frame, width=30, font=12, show="*")
    pass_entry.grid(row=3, column=0, pady=(0,20))

    status = tk.Label(current_window, text="", fg="red", font=11)
    status.pack(pady=10)

    def do_login():
        global username
        username = user_entry.get().strip()
        pwd = pass_entry.get().strip()
        if not username or not pwd:
            status.config(text="Vui lòng nhập đầy đủ!")
            return
        try:
            client.send(f"LOGIN|{username}|{pwd}".encode("utf-8"))
            result = client.recv(1024).decode("utf-8").strip()
            if result == "SUCCESS":
                status.config(text="Đăng nhập thành công!", fg="green")
                current_window.after(800, open_chat)
            else:
                status.config(text="Sai tài khoản hoặc mật khẩu!")
        except:
            status.config(text="Lỗi kết nối server!")

    tk.Button(current_window, text="Đăng nhập", command=do_login, bg="#27ae60", fg="white", width=25, height=2).pack(pady=20)
    tk.Button(current_window, text="Chưa có tài khoản? Đăng ký ngay", fg="#2980b9", bd=0, cursor="hand2", command=register_screen).pack(pady=5)

    current_window.bind('<Return>', lambda e: do_login())
    current_window.mainloop()

# ====================== MÀN HÌNH CHAT ======================
def open_chat():
    global current_window
    if current_window:
        current_window.destroy()

    root = tk.Tk()
    root.title(f"Chat App - {username}")
    root.geometry("600x700")
    root.configure(bg="#f0f2f5")

    chat_box = scrolledtext.ScrolledText(root, state=tk.DISABLED, bg="white", font=("Arial", 11))
    chat_box.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

    typing_label = tk.Label(root, text="", fg="gray", font=("Arial", 9), anchor="w", bg="#f0f2f5")
    typing_label.pack(fill=tk.X, padx=15)

    input_frame = tk.Frame(root, bg="#f0f2f5")
    input_frame.pack(fill=tk.X, padx=15, pady=(0,15))

    entry = tk.Entry(input_frame, font=("Arial", 11), relief=tk.FLAT, bg="white", bd=5)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10)

    def on_typing(event=None):
        global is_typing
        if not is_typing and entry.get().strip():
            is_typing = True
            try:
                client.send(f"__TYPING__:{username}\n".encode("utf-8"))
            except:
                pass

    def stop_typing(event=None):
        global is_typing
        if is_typing:
            is_typing = False
            try:
                client.send(f"__STOP_TYPING__:{username}\n".encode("utf-8"))
            except:
                pass

    def send_msg(event=None):
        msg = entry.get().strip()
        if msg:
            stop_typing()
            full_msg = f"{username}: {msg}\n"
            try:
                client.send(full_msg.encode("utf-8"))
                 # Local echo thủ công để tránh lặp
                chat_box.config(state=tk.NORMAL)
                chat_box.insert(tk.END, username + "\n", "me_name")
                chat_box.insert(tk.END, msg + "\n\n", "me_msg")
                chat_box.config(state=tk.DISABLED)
                chat_box.see(tk.END)
            except:
                messagebox.showerror("Lỗi", "Không gửi được!")
            entry.delete(0, tk.END)

    entry.bind("<Key>", on_typing)
    entry.bind("<Return>", send_msg)
    entry.bind("<FocusOut>", stop_typing)

    send_btn = tk.Button(input_frame, text="Gửi", command=send_msg, bg="#0084ff", fg="white", width=10)
    send_btn.pack(side=tk.RIGHT, padx=(10,0))

    # Tag định dạng
    chat_box.tag_config("me_name", foreground="#0084ff", font=("Arial", 10, "bold"), justify="right")
    chat_box.tag_config("me_msg", foreground="#0084ff", justify="right")
    chat_box.tag_config("other_name", foreground="black", font=("Arial", 10, "bold"), justify="left")
    chat_box.tag_config("other_msg", foreground="black", justify="left")
    chat_box.tag_config("system", foreground="gray", font=("Arial", 9, "italic"), justify="center")

    def display_message(msg, is_me=False):
        chat_box.config(state=tk.NORMAL)
        if ": " in msg:
            sender, content = msg.split(": ", 1)
            if is_me:  # Chỉ dùng cho local echo
                chat_box.insert(tk.END, sender + "\n", "me_name")
                chat_box.insert(tk.END, content + "\n\n", "me_msg")
            elif sender == username:
                # Tin của mình từ server → bỏ qua, đã local echo rồi
                pass
            else:
                # Tin người khác
                chat_box.insert(tk.END, sender + "\n", "other_name")
                chat_box.insert(tk.END, content + "\n\n", "other_msg")
        else:
            # Thông báo hệ thống
            chat_box.insert(tk.END, msg + "\n\n", "system")
        chat_box.config(state=tk.DISABLED)
        chat_box.see(tk.END)

    display_message(f"🌟 Chào mừng {username} đến với phòng chat!")

    def receive():
        buffer = ""
        while True:
            try:
                data = client.recv(1024)
                if not data:
                    display_message("⚠️ Mất kết nối với server")
                    break
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        if line.startswith("__TYPING__:"):
                            name = line[11:]
                            if name != username:
                                typing_label.config(text=f"{name} đang gõ...")
                        elif line.startswith("__STOP_TYPING__:"):
                            name = line[15:]
                            if name != username:
                                typing_label.config(text="")
                        else:
                            display_message(line)  # Không truyền is_me=True → sẽ bỏ qua nếu là tin của mình
            except:
                display_message("⚠️ Mất kết nối với server")
                break

    threading.Thread(target=receive, daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

# Bắt đầu từ màn hình đăng nhập
login_screen()