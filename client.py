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

# ===== BÁO ĐANG GÕ =====
typing_users = {}
is_typing = False
typing_timer = None

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

FLY_EMOJI_KEYWORDS = ["❤️", "🔥", "👍", "😄", "😢", "😃", "😉"]

def replace_emoji(text):
    for k, v in EMOJI_MAP.items():
        text = text.replace(k, v)
    return text

# ===== FLY EMOJI =====
def fly_emoji(emoji):
    lbl = tk.Label(root, text=emoji, font=("Arial", 24))
    lbl.place(x=random.randint(20, 350), y=450)

    def animate(y):
        if y < 0:
            lbl.destroy()
            return
        lbl.place(y=y)
        root.after(30, lambda: animate(y - 10))

    animate(450)

def check_fly_effect(text):
    for emoji in FLY_EMOJI_KEYWORDS:
        if emoji in text:
            fly_emoji(emoji)

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
        try:
            client.send(f"REGISTER|{u}|{p}".encode())
            if client.recv(1024).decode() == "SUCCESS":
                current_window.after(500, login_screen)
            else:
                status.config(text="Tài khoản đã tồn tại")
        except:
            status.config(text="Mất kết nối với server!")

    tk.Button(current_window, text="Đăng ký",
              command=do_register, width=20).pack(pady=20)
    tk.Button(current_window, text="← Quay lại",
              command=login_screen).pack()

    user_entry.focus()
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

        # Thông báo trống
        if not username or not pwd:
            status.config(text="Vui lòng nhập đầy đủ thông tin!")
            return
        
        #Xử lý trong quá trình đăng nhập
        try:
            client.send(f"LOGIN|{username}|{pwd}".encode("utf-8"))
            result = client.recv(1024).decode("utf-8").strip()
            if result == "SUCCESS":
                status.config(text="Đăng nhập thành công!", fg="green")
                current_window.after(1000, open_chat)
            else:
                status.config(text="Sai tên đăng nhập hoặc mật khẩu!")
        except:
            status.config(text="Mất kết nối với server!")
            
        # client.send(f"LOGIN|{username}|{pwd}".encode())
        # if client.recv(1024).decode() == "SUCCESS":
        #     current_window.after(500, open_chat)
        # else:
        #     status.config(text="Sai thông tin")

    tk.Button(current_window, text="Đăng nhập",
              command=do_login, width=20).pack(pady=20)
    tk.Button(current_window, text="Chưa có tài khoản? Đăng ký ngay",
              command=register_screen, fg="blue", bd=0).pack()

    #user_entry.focus()
    
    current_window.bind("<Return>", lambda e: do_login())
    current_window.mainloop()

# ================= CHAT =================
def open_chat():
    global root, current_window
    if current_window:
        current_window.destroy()

    #Giao diện
    root = tk.Tk()
    root.title(f"Chat App - {username}")
    root.geometry("600x700")
    root.configure(bg="#f0f2f5")

    chat_box = scrolledtext.ScrolledText(
        root, state=tk.DISABLED, font=("Arial", 11))
    chat_box.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

    input_frame = tk.Frame(root)
    input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

    entry = tk.Entry(input_frame)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    entry.bind("<KeyPress>", lambda e: send_typing())

    send_btn = tk.Button(input_frame, text="Gửi", width=10)
    send_btn.pack(side=tk.RIGHT)

#============THU HỒI TIN NHẮN=============
    def recall_message(event): #nháy đúp 3 lần
        try:
            index = chat_box.index(f"@{event.x},{event.y}")
            line = int(index.split(".")[0])
            tags = chat_box.tag_names(index)

            if not any(t in tags for t in ("name_me", "msg_me", "time_me")):
                return

            chat_box.config(state=tk.NORMAL)
            chat_box.delete(f"{line}.0", f"{line + 4}.0")
            chat_box.config(state=tk.DISABLED)
        except:
            pass

    chat_box.bind("<Double-Button-1>", recall_message)

    # ============HIỂN THI "ĐANG NHẬP..."=============
    typing_label = tk.Label(
        root,
        text="",
        font=("Arial", 9, "italic"),
        fg="gray"
    )
    typing_label.pack(anchor="w", padx=18, pady=(0, 5))

    # ============ HÀM CẬP NHẬT NỘI DUNG HIỂN THị ĐANG NHẬP=============
    def update_typing_label():
        if typing_users:
            typing_label.config(
                text=", ".join(typing_users.keys()) + " đang nhập tin nhắn..."
            )
        else:
            typing_label.config(text="")
    
    #TAG
    chat_box.tag_config("name_me", justify="right", font=("Arial", 11, "bold"), foreground="#0084ff")
    chat_box.tag_config("name_other", justify="left", font=("Arial", 11, "bold"))
    chat_box.tag_config("msg_me", justify="right")
    chat_box.tag_config("msg_other", justify="left")
    chat_box.tag_config("time_me", justify="right", font=("Arial", 8), foreground="gray")
    chat_box.tag_config("time_other", justify="left", font=("Arial", 8), foreground="gray")
    chat_box.tag_config("system", foreground="gray", font=("Arial", 9, "italic"), justify="center")

    my_avatar = get_avatar_by_username(username)

    # ============GỬI TRẠNG THÁI ĐANG GÕ=============
    #typing_timer = None

    def send_typing():
        global is_typing, typing_timer

        if not is_typing:
            try:
                client.send(f"TYPING|{username}\n".encode())
            except:
                pass
            is_typing = True

        if typing_timer:
            root.after_cancel(typing_timer)

        typing_timer = root.after(1500, stop_typing)

    # ============GỬI TRẠNG THÁI DỪNG GÕ=============
    def stop_typing():
        global is_typing
        if is_typing:
            try:
                client.send(f"STOP_TYPING|{username}\n".encode())
            except:
                pass
            is_typing = False

    def send_msg(event=None):
        msg = entry.get().strip()
        if not msg:
            return
        stop_typing() #-> stop typing trước khi gởi, k bị hiển thị liên tục

        msg = replace_emoji(msg)
        check_fly_effect(msg)   # THÊM EMOJI BAY

        full_smg = f"{username}: {msg}\n"
        try:    #Chống crack
            client.send(f"{username}: {msg}\n".encode())
            winsound.MessageBeep()  #Âm thanh gởi tin nhắn

            t = datetime.now().strftime("%H:%M")

            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"{my_avatar} {username}\n", "name_me")
            chat_box.insert(tk.END, msg + "\n", "msg_me")
            chat_box.insert(tk.END, t + "\n\n", "time_me")
            chat_box.config(state=tk.DISABLED)
            chat_box.see(tk.END)
        except:
            messagebox.showerror("Lỗi", "Không gửi được tin nhắn!")

        entry.delete(0, tk.END)
        #stop_typing()
    
    #Xử lý socket
        #--- Xử lý hiển thị
    def display_message(line = None, system = False):
        chat_box.config(state=tk.NORMAL)
        if system:
            chat_box.insert(tk.END, line + "\n\n", "system")
        elif line and ": " in line:
            sender, content = line.split(": ", 1)
            if sender == username:  #Bỏ hiển thị tin nhắn bản thân, k bị lặp (đã local echo)
                return
            
            content = replace_emoji(content)
            check_fly_effect(content)   #  EMOJI BAY KHI NHẬN

            avatar = get_avatar_by_username(sender)
            t = datetime.now().strftime("%H:%M")

            #chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"{avatar} {sender}\n", "name_other")
            chat_box.insert(tk.END, content + "\n", "msg_other")
            chat_box.insert(tk.END, t + "\n\n", "time_other")
            winsound.MessageBeep()  # Âm thông báo khi nhận tin

        chat_box.config(state=tk.DISABLED)
        chat_box.see(tk.END)
            

        #--- Xử lý nhận - phân loại dữ liệu, xử lý typing
    def receive():
        buf = ""
        while True:
            try:    #Xử lý lỗi sever ngắt kết nối đột ngột làm chết sever/ client   
                data = client.recv(1024)    
                if not data:
                    break
                buf += data.decode("utf-8") #gom dữ liệu, nếu k sẽ bị TCP chia nhỏ gói, thất thoái dữ liệu
                
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip() #Sửa lỗi dòng rỗng khi gởi

                    # ===== NHẬN TRẠNG THÁI BẮT ĐẦU VÀ KẾT THÚC GÕ ===== Xử lý typing
                    if line.startswith("TYPING|"):
                        sender = line.split("|", 1)[1]
                        if sender != username:
                            typing_users[sender] = True
                            root.after(0, update_typing_label)
                        continue

                    # Xử lý typing 2
                    if line.startswith("STOP_TYPING|"):
                        sender = line.split("|", 1)[1]
                        if sender != username:
                            typing_users.pop(sender, None)
                            root.after(0, update_typing_label)
                        continue

                    #Tin nhắn bình thường (my send) -> đem về display_msg()
                    display_message(line)
                    # if ": " in line:
                    #     sender, content = line.split(": ", 1)
                    #     if sender == username:  #Bỏ hiển thị tin nhắn bản thân, k bị lặp
                    #         continue

                    #     content = replace_emoji(content)
                    #     check_fly_effect(content)   #  EMOJI BAY KHI NHẬN

                    #     avatar = get_avatar_by_username(sender)
                    #     t = datetime.now().strftime("%H:%M")

                    #     chat_box.config(state=tk.NORMAL)
                    #     chat_box.insert(tk.END, f"{avatar} {sender}\n", "name_other")
                    #     chat_box.insert(tk.END, content + "\n", "msg_other")
                    #     chat_box.insert(tk.END, t + "\n\n", "time_other")
                    #     chat_box.config(state=tk.DISABLED)
                    #     chat_box.see(tk.END)
                    #     winsound.MessageBeep()  # Âm thông báo khi nhận tin

            except Exception as e:
                print("Lỗi nhận dữ liệu:", e)
                break
    
         # Khi ra khỏi vòng lặp → server ngắt → đóng app (Mất kết nối đến sever)
        root.after(0, lambda: messagebox.showinfo("Ngắt kết nối", "Mất kết nối đến server!") or root.destroy())
    
    #   Chào mừng
    display_message(f"🌟 Chào mừng {username} đến với phòng chat!", system=True)

    entry.bind("<Return>", send_msg)
    send_btn.config(command=send_msg)
    threading.Thread(target=receive, daemon=True).start()
    root.mainloop()

# ================= START =================
login_screen()
