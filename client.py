import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

HOST = "127.0.0.1"
PORT = 12345
is_typing = False

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((HOST, PORT))
except:
    messagebox.showerror("Lỗi", "Không kết nối được server")
    exit()

def receive():
    while True:
        try:
            msg = client.recv(1024).decode("utf-8").strip()
            if msg.startswith("__TYPING__:"):
                name = msg.replace("__TYPING__:", "")
                if name != username:
                    typing_label.config(text=f"{name} đang gõ...")
                continue

            if msg.startswith("__STOP_TYPING__:"):
                name = msg.replace("__STOP_TYPING__:", "")
                if name != username:
                    typing_label.config(text="")
                continue
            if not msg:
                continue

            # Tách username và nội dung
            if ": " in msg:
                sender, content = msg.split(": ", 1)
            else:
                sender = ""
                content = msg

            chat_box.config(state=tk.NORMAL)

            if sender == username:
                # TÊN (in đậm)
                chat_box.insert(tk.END, sender + "\n", "me_name")
                # NỘI DUNG
                chat_box.insert(tk.END, content + "\n\n", "me_msg")
            else:
                chat_box.insert(tk.END, sender + "\n", "other_name")
                chat_box.insert(tk.END, content + "\n\n", "other_msg")

            chat_box.config(state=tk.DISABLED)
            chat_box.yview(tk.END)

        except:
            break

def on_typing(event):
    global is_typing
    if not is_typing:
        is_typing = True
        client.send(f"__TYPING__:{username}\n".encode("utf-8"))

def stop_typing(event=None):
    global is_typing
    if is_typing:
        is_typing = False
        client.send(f"__STOP_TYPING__:{username}\n".encode("utf-8"))

def send(event=None):
    msg = entry.get()
    if msg:
        stop_typing()
        client.send((username + ": " + msg + "\n").encode("utf-8"))
        entry.delete(0, tk.END)

def on_close():
    client.close()
    root.destroy()

# ===== GUI =====
root = tk.Tk()
root.title("Chat App - Tkinter")
root.geometry("400x500")

username = simpledialog.askstring(
    "Tên", "Nhập tên của bạn:", parent=root
)

if not username:
    username = "Guest"

chat_box = scrolledtext.ScrolledText(
    root,
    state=tk.DISABLED,
    wrap=tk.WORD
)
chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
typing_label = tk.Label(
    root,
    text="",
    fg="gray",
    anchor="w"
)
typing_label.pack(fill=tk.X, padx=10)

# ===== TAG MÀU & ĐỊNH DẠNG =====
chat_box.tag_config(
    "me_name",
    foreground="blue",
    font=("Arial", 10, "bold"),
    justify="right"
)

chat_box.tag_config(
    "me_msg",
    foreground="blue",
    justify="right"
)

chat_box.tag_config(
    "other_name",
    foreground="black",
    font=("Arial", 10, "bold"),
    justify="left"
)

chat_box.tag_config(
    "other_msg",
    foreground="black",
    justify="left"
)

entry = tk.Entry(root)
entry.pack(fill=tk.X, padx=10)
entry.bind("<Key>", on_typing)
entry.bind("<Return>", stop_typing)
entry.bind("<FocusOut>", stop_typing)

send_btn = tk.Button(root, text="Gửi", command=send)
send_btn.pack(pady=5)

threading.Thread(target=receive, daemon=True).start()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
