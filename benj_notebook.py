# benj_notebook.py - 完整版（钱 + 时间 + 文章 + 数据库查看器）
# 打包命令  
# pyinstaller --onefile --noconsole --name "benj_notebook" --icon "myicon.ico" --add-data "myicon.ico;." benj_notebook.py

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import base64
import hashlib
import os
import sys
from cryptography.fernet import Fernet

# ========== 配置 ==========
DB_PATH = os.path.join(os.path.expanduser("~"), "b")

# 资源路径（兼容打包后）
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 颜色配置
COLORS = {
    "bg": "#ffffff",
    "button_bg": "#f5f5f5",
    "button_fg": "#333333",
    "border": "#dddddd",
    "active_bg": "#e8e8e8",
    "income": "#d32f2f",
    "expense": "#2e7d32",
    "text": "#333333",
    "placeholder": "#bbbbbb",
}

# 字体配置
FONT = ("微软雅黑", 12)
FONT_SMALL = ("微软雅黑", 11)
FONT_TITLE = ("微软雅黑", 14)

# 分类配置
MONEY_TYPES = ["收入", "吃喝", "交通", "日用", "娱乐", "基建", "房贷", "赞助", "医疗", "其他"]
NOTEBOOK_CATEGORIES = ["当下", "存档", "精选助手问与答"]
MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# 全局密钥（登录时设置）
SECRET_KEY = ""

# ========== 加密工具 ==========
def get_cipher():
    key = hashlib.sha256(SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)

def encrypt_data(text):
    if not text:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(str(text).encode()).decode()

def decrypt_data(encrypted_text):
    if not encrypted_text:
        return ""
    try:
        cipher = get_cipher()
        return cipher.decrypt(encrypted_text.encode()).decode()
    except:
        return encrypted_text

# ========== 数据库操作 ==========
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS money (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            amount REAL NOT NULL,
            memo TEXT DEFAULT '',
            type TEXT DEFAULT '其他',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notebook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            category TEXT DEFAULT '存档',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            pin_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()

# ========== PIN验证 ==========
def verify_pin(input_pin):
    """验证PIN并设置密钥"""
    global SECRET_KEY
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pin_hash FROM user WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return False
    
    input_hash = hashlib.sha256(input_pin.encode()).hexdigest()
    if input_hash == row["pin_hash"]:
        SECRET_KEY = input_pin  # PIN就是密钥
        return True
    return False

# ========== 记账操作 ==========
def money_add(time, amount, memo, type_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO money (time, amount, memo, type) VALUES (?, ?, ?, ?)",
        (time, amount, encrypt_data(memo), type_name)
    )
    conn.commit()
    conn.close()

def money_delete(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM money WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def money_get_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM money ORDER BY time DESC")
    records = cursor.fetchall()
    conn.close()
    result = []
    for record in records:
        record_dict = dict(record)
        record_dict["memo"] = decrypt_data(record_dict["memo"])
        result.append(record_dict)
    return result

def money_get_years():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT substr(time, 1, 4) as year FROM money ORDER BY year DESC")
    years = [row["year"] for row in cursor.fetchall()]
    conn.close()
    return years

# ========== 存档操作 ==========
def notebook_add(title, content, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notebook (title, content, category) VALUES (?, ?, ?)",
        (encrypt_data(title), encrypt_data(content), category)
    )
    conn.commit()
    conn.close()

def notebook_update(note_id, title, content, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notebook SET title = ?, content = ?, category = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (encrypt_data(title), encrypt_data(content), category, note_id)
    )
    conn.commit()
    conn.close()

def notebook_delete(note_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notebook WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def notebook_get_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notebook ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()
    result = []
    for record in records:
        record_dict = dict(record)
        record_dict["title"] = decrypt_data(record_dict["title"])
        record_dict["content"] = decrypt_data(record_dict["content"])
        result.append(record_dict)
    return result

# ========== 时间记录操作 ==========
def time_add(date, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO time (date, content) VALUES (?, ?)",
        (date, encrypt_data(content))
    )
    conn.commit()
    conn.close()

def time_delete(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM time WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def time_get_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM time ORDER BY date DESC")
    records = cursor.fetchall()
    conn.close()
    result = []
    for record in records:
        record_dict = dict(record)
        record_dict["content"] = decrypt_data(record_dict["content"])
        result.append(record_dict)
    return result

def time_get_years():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT substr(date, 1, 4) as year FROM time ORDER BY year DESC")
    years = [row["year"] for row in cursor.fetchall()]
    conn.close()
    return years

# ========== 数据库查看器操作 ==========
def db_get_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()
    return tables

def db_get_table_count(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    count = cursor.fetchone()["count"]
    conn.close()
    return count

def db_get_table_data(table_name, offset=0, limit=500):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
    records = [dict(row) for row in cursor.fetchall()]
    
    columns = []
    if records:
        columns = list(records[0].keys())
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row["name"] for row in cursor.fetchall()]
    
    conn.close()
    return columns, records

# ========== PIN验证窗口 ==========
def pin_verify_window():
    verify_win = tk.Tk()
    verify_win.withdraw()                                  # === 先隐藏 ===
    try:
        verify_win.iconbitmap(resource_path("myicon.ico"))
    except Exception:
        pass
    verify_win.title("")
    verify_win.configure(bg=COLORS["bg"])
    verify_win.resizable(False, False)

    tk.Label(verify_win, text="PIN", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITLE).pack(pady=20)
    pin_entry = tk.Entry(verify_win, show="*", font=FONT, width=15, justify="center", relief="solid", bd=1)
    pin_entry.pack(pady=10)

    def check_pin(event=None):
        input_pin = pin_entry.get().strip()
        if verify_pin(input_pin):
            verify_win.destroy()
            create_main_window()
        else:
            messagebox.showwarning("错误", "PIN错误")
            pin_entry.delete(0, tk.END)
            pin_entry.focus()
            pin_entry.focus_force()

    pin_entry.bind("<Return>", check_pin)
    tk.Button(verify_win, text="确定", command=check_pin, font=FONT,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=20, pady=2, takefocus=False).pack(pady=10)

    # === 布局完，算好位置，再一次性显示 ===
    verify_win.update_idletasks()
    x = (verify_win.winfo_screenwidth() // 2) - 150
    y = (verify_win.winfo_screenheight() // 2) - 90
    verify_win.geometry(f"300x180+{x}+{y}")
    verify_win.deiconify()

    # === 显示之后再抢焦点，确保光标在输入框 ===
    verify_win.lift()
    verify_win.attributes("-topmost", True)
    verify_win.after(10, lambda: verify_win.attributes("-topmost", False))
    pin_entry.focus_set()
    pin_entry.focus_force()

    verify_win.mainloop()

# ========== 记账页面 ==========
def create_money_page(parent, back_callback):
    for widget in parent.winfo_children():
        widget.destroy()

    filter_state = {
        "year": datetime.datetime.now().strftime("%Y"),
        "month": datetime.datetime.now().strftime("%m"),
        "hide_special": False
    }

    top_frame = tk.Frame(parent, bg=COLORS["bg"])
    top_frame.pack(fill="x", padx=10, pady=5)
    tk.Button(top_frame, text="← 返回", command=back_callback, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left")

    add_frame = tk.Frame(parent, bg=COLORS["bg"])
    add_frame.pack(fill="x", padx=10, pady=10)

    tk.Label(add_frame, text="日期", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    date_entry = tk.Entry(add_frame, font=FONT, width=12, relief="solid", bd=1)
    date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
    date_entry.pack(side="left", padx=(0,10))

    tk.Label(add_frame, text="金额", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    amount_entry = tk.Entry(add_frame, font=FONT, width=10, relief="solid", bd=1)
    amount_entry.pack(side="left", padx=(0,10))

    tk.Label(add_frame, text="分类", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    type_var = tk.StringVar(value="吃喝")
    type_combo = ttk.Combobox(add_frame, textvariable=type_var, values=MONEY_TYPES, font=FONT, width=8, state="readonly")
    type_combo.pack(side="left", padx=(0,10))

    tk.Label(add_frame, text="备注", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    memo_entry = tk.Entry(add_frame, font=FONT, width=25, relief="solid", bd=1)
    memo_entry.pack(side="left", padx=(0,10))

    def add_record():
        date = date_entry.get().strip()
        amount_str = amount_entry.get().strip()
        memo = memo_entry.get().strip()
        type_name = type_var.get()
        if not date:
            messagebox.showwarning("提示", "请输入日期")
            return
        if not amount_str:
            messagebox.showwarning("提示", "请输入金额")
            return
        try:
            amount = float(amount_str)
        except:
            messagebox.showwarning("提示", "金额格式错误")
            return
        if type_name not in ("收入", "赞助") and amount > 0:
            amount = -amount
        money_add(date, amount, memo, type_name)
        amount_entry.delete(0, tk.END)
        memo_entry.delete(0, tk.END)
        type_var.set("吃喝")
        load_records()

    tk.Button(add_frame, text="记", command=add_record, font=FONT,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=15, pady=2, takefocus=False).pack(side="left")

    memo_entry.bind("<Return>", lambda e: add_record())
    amount_entry.bind("<Return>", lambda e: add_record())

    filter_frame = tk.Frame(parent, bg=COLORS["bg"])
    filter_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(filter_frame, text="年份", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    year_var = tk.StringVar(value=filter_state["year"])
    year_combo = ttk.Combobox(filter_frame, textvariable=year_var, font=FONT, width=10, state="readonly")
    year_combo.pack(side="left", padx=(0,10))

    tk.Label(filter_frame, text="月份", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    month_var = tk.StringVar(value=filter_state["month"])
    month_combo = ttk.Combobox(filter_frame, textvariable=month_var, values=["全部月份"] + MONTHS, font=FONT, width=10, state="readonly")
    month_combo.pack(side="left", padx=(0,10))

    def apply_filter():
        filter_state["year"] = "" if year_var.get() == "全部年份" else year_var.get()
        filter_state["month"] = "" if month_var.get() == "全部月份" else month_var.get()
        load_records()

    tk.Button(filter_frame, text="筛选", command=apply_filter, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left", padx=(0,5))

    def reset_filter():
        now = datetime.datetime.now()
        year_var.set(now.strftime("%Y"))
        month_var.set(now.strftime("%m"))
        filter_state["year"] = year_var.get()
        filter_state["month"] = month_var.get()
        load_records()

    tk.Button(filter_frame, text="重置", command=reset_filter, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left", padx=(0,5))

    def toggle_special():
        filter_state["hide_special"] = not filter_state["hide_special"]
        btn_toggle.config(text="显示房贷+赞助" if filter_state["hide_special"] else "隐藏房贷+赞助")
        load_records()

    btn_toggle = tk.Button(filter_frame, text="隐藏房贷+赞助", command=toggle_special, font=FONT_SMALL,
                           relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                           activebackground=COLORS["active_bg"], cursor="hand2",
                           highlightthickness=1, highlightbackground=COLORS["border"],
                           padx=10, pady=2, takefocus=False)
    btn_toggle.pack(side="left", padx=(0,5))

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        item = tree.item(selected[0])
        record_id = item["tags"][0] if item["tags"] else None
        if record_id and messagebox.askyesno("确认", "确定删除这条记录？"):
            money_delete(int(record_id))
            load_records()

    tk.Button(filter_frame, text="删除选中", command=delete_selected, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left")

    summary_frame = tk.Frame(parent, bg=COLORS["bg"])
    summary_frame.pack(fill="x", padx=10, pady=10)

    income_label = tk.Label(summary_frame, text="收入：0.00", bg=COLORS["bg"], fg=COLORS["income"], font=FONT_SMALL)
    income_label.pack(side="left", padx=(0,20))
    expense_label = tk.Label(summary_frame, text="支出：0.00", bg=COLORS["bg"], fg=COLORS["expense"], font=FONT_SMALL)
    expense_label.pack(side="left", padx=(0,20))
    balance_label = tk.Label(summary_frame, text="结余：0.00", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL)
    balance_label.pack(side="left")

    table_frame = tk.Frame(parent, bg=COLORS["bg"])
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    scrollbar = tk.Scrollbar(table_frame)
    scrollbar.pack(side="right", fill="y")

    style = ttk.Style()
    style.configure("Treeview", font=FONT, rowheight=25)
    style.configure("Treeview.Heading", font=FONT_SMALL)

    columns = ("date", "amount", "type", "memo")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
    tree.heading("date", text="日期")
    tree.heading("amount", text="金额")
    tree.heading("type", text="分类")
    tree.heading("memo", text="备注")
    tree.column("date", width=120)
    tree.column("amount", width=100, anchor="e")
    tree.column("type", width=80)
    tree.column("memo", width=400)
    tree.pack(fill="both", expand=True)
    scrollbar.config(command=tree.yview)

    tree.bind("<Delete>", lambda e: delete_selected())

    stats_frame = tk.Frame(parent, bg=COLORS["bg"])
    stats_frame.pack(fill="x", padx=10, pady=10)

    income_stats_frame = tk.Frame(stats_frame, bg=COLORS["bg"])
    income_stats_frame.pack(side="left", fill="both", expand=True, padx=(0,10))
    tk.Label(income_stats_frame, text="收入分类", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL).pack(anchor="w")
    income_canvas = tk.Canvas(income_stats_frame, height=150, bg=COLORS["bg"], highlightthickness=0)
    income_canvas.pack(fill="x")

    expense_stats_frame = tk.Frame(stats_frame, bg=COLORS["bg"])
    expense_stats_frame.pack(side="left", fill="both", expand=True, padx=(10,0))
    tk.Label(expense_stats_frame, text="支出分类", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL).pack(anchor="w")
    expense_canvas = tk.Canvas(expense_stats_frame, height=150, bg=COLORS["bg"], highlightthickness=0)
    expense_canvas.pack(fill="x")

    def load_records():
        for item in tree.get_children():
            tree.delete(item)
        records = money_get_all()
        filtered = []
        total_in = 0
        total_out = 0
        for record in records:
            time = record["time"]
            amount = record["amount"]
            type_name = record["type"]
            if filter_state["year"] and not time.startswith(filter_state["year"]):
                continue
            if filter_state["month"] and time[5:7] != filter_state["month"]:
                continue
            if filter_state["hide_special"] and type_name in ["房贷", "赞助"]:
                continue
            filtered.append(record)
            if amount > 0:
                total_in += amount
            else:
                total_out += abs(amount)
        income_label.config(text=f"收入：{total_in:.2f}")
        expense_label.config(text=f"支出：{total_out:.2f}")
        balance = total_in - total_out
        balance_label.config(text=f"结余：{'+' if balance >= 0 else ''}{balance:.2f}",
                             fg=COLORS["income"] if balance >= 0 else COLORS["expense"])
        for record in filtered:
            amount = record["amount"]
            tag = "income" if amount > 0 else "expense"
            tree.insert("", "end", values=(record["time"], f"{amount:.2f}", record["type"], record["memo"]),
                        tags=(str(record["id"]), tag))
        tree.tag_configure("income", foreground=COLORS["income"])
        tree.tag_configure("expense", foreground=COLORS["expense"])
        draw_stats(filtered)

    def draw_stats(records):
        income_canvas.delete("all")
        expense_canvas.delete("all")
        income_map = {}
        expense_map = {}
        for rec in records:
            amt = rec["amount"]
            typ = rec["type"]
            if amt > 0:
                income_map[typ] = income_map.get(typ, 0) + amt
            else:
                expense_map[typ] = expense_map.get(typ, 0) + abs(amt)
        income_items = sorted(income_map.items(), key=lambda x: x[1], reverse=True)
        expense_items = sorted(expense_map.items(), key=lambda x: x[1], reverse=True)
        draw_bars(income_canvas, income_items, COLORS["income"])
        draw_bars(expense_canvas, expense_items, COLORS["expense"])

    def draw_bars(canvas, items, color):
        if not items:
            canvas.create_text(10, 10, anchor="w", text="暂无数据", fill=COLORS["placeholder"], font=FONT_SMALL)
            return
        max_val = max([val for _, val in items])
        bar_height = 18
        gap = 8
        y = 5
        label_width = 50
        bar_start_x = label_width + 10
        max_bar_width = 150
        for label, val in items:
            text_y = y + bar_height // 2
            canvas.create_text(label_width - 5, text_y, anchor="e", text=label, fill=COLORS["text"], font=FONT_SMALL)
            bar_width = int((val / max_val) * max_bar_width)
            canvas.create_rectangle(bar_start_x, y, bar_start_x + bar_width, y + bar_height, fill=color, outline="")
            canvas.create_text(bar_start_x + bar_width + 5, text_y, anchor="w", text=f"{val:.2f}", fill=COLORS["text"], font=FONT_SMALL)
            y += bar_height + gap
        canvas.config(height=y + 10)

    def load_years():
        years = money_get_years()
        year_combo["values"] = ["全部年份"] + years

    load_years()
    load_records()

# ========== 时间记录页面 ==========
def create_time_page(parent, back_callback):
    for widget in parent.winfo_children():
        widget.destroy()

    filter_state = {
        "year": datetime.datetime.now().strftime("%Y"),
        "month": datetime.datetime.now().strftime("%m"),
        "sort": "desc",
        "keyword": ""
    }
    current_records = []

    top_frame = tk.Frame(parent, bg=COLORS["bg"])
    top_frame.pack(fill="x", padx=10, pady=5)
    tk.Button(top_frame, text="← 返回", command=back_callback, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left")

    input_frame = tk.Frame(parent, bg=COLORS["bg"])
    input_frame.pack(fill="x", padx=10, pady=10)

    date_entry = tk.Entry(input_frame, font=FONT, width=12, relief="solid", bd=1)
    date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
    date_entry.pack(side="left", padx=(0,10))

    content_entry = tk.Entry(input_frame, font=FONT, width=50, relief="solid", bd=1)
    content_entry.pack(side="left", padx=(0,10))

    def save_record():
        date = date_entry.get().strip()
        content = content_entry.get().strip()
        if not date:
            messagebox.showwarning("提示", "请输入日期")
            return
        if not content:
            messagebox.showwarning("提示", "请输入内容")
            return
        time_add(date, content)
        content_entry.delete(0, tk.END)
        load_records()

    tk.Button(input_frame, text="记", command=save_record, font=FONT,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=15, pady=2, takefocus=False).pack(side="left")

    content_entry.bind("<Return>", lambda e: save_record())

    filter_frame = tk.Frame(parent, bg=COLORS["bg"])
    filter_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(filter_frame, text="年份", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    year_var = tk.StringVar(value=filter_state["year"])
    year_combo = ttk.Combobox(filter_frame, textvariable=year_var, font=FONT, width=10, state="readonly")
    year_combo.pack(side="left", padx=(0,10))

    tk.Label(filter_frame, text="月份", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    month_var = tk.StringVar(value=filter_state["month"])
    month_combo = ttk.Combobox(filter_frame, textvariable=month_var, values=["全部月份"] + MONTHS, font=FONT, width=10, state="readonly")
    month_combo.pack(side="left", padx=(0,10))

    tk.Label(filter_frame, text="排序", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    sort_var = tk.StringVar(value="新→旧")
    sort_combo = ttk.Combobox(filter_frame, textvariable=sort_var, values=["新→旧", "旧→新"], font=FONT, width=8, state="readonly")
    sort_combo.pack(side="left", padx=(0,10))

    tk.Label(filter_frame, text="搜索", bg=COLORS["bg"], font=FONT_SMALL).pack(side="left", padx=(0,5))
    keyword_entry = tk.Entry(filter_frame, font=FONT, width=20, relief="solid", bd=1)
    keyword_entry.pack(side="left", padx=(0,10))

    def apply_filter():
        filter_state["year"] = "" if year_var.get() == "全部年份" else year_var.get()
        filter_state["month"] = "" if month_var.get() == "全部月份" else month_var.get()
        filter_state["sort"] = "desc" if sort_var.get() == "新→旧" else "asc"
        filter_state["keyword"] = keyword_entry.get().strip().lower()
        load_records()

    tk.Button(filter_frame, text="筛选", command=apply_filter, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left", padx=(0,5))

    def reset_filter():
        now = datetime.datetime.now()
        year_var.set(now.strftime("%Y"))
        month_var.set(now.strftime("%m"))
        sort_var.set("新→旧")
        keyword_entry.delete(0, tk.END)
        filter_state["year"] = now.strftime("%Y")
        filter_state["month"] = now.strftime("%m")
        filter_state["sort"] = "desc"
        filter_state["keyword"] = ""
        load_records()

    tk.Button(filter_frame, text="重置", command=reset_filter, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left")

    search_info_label = tk.Label(parent, text="", bg=COLORS["bg"], fg="#888888", font=FONT_SMALL)
    search_info_label.pack(fill="x", padx=10, pady=2)

    table_frame = tk.Frame(parent, bg=COLORS["bg"])
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    scrollbar = tk.Scrollbar(table_frame)
    scrollbar.pack(side="right", fill="y")

    style = ttk.Style()
    style.configure("Treeview", font=FONT, rowheight=25)
    style.configure("Treeview.Heading", font=FONT_SMALL)

    # 只保留一列：日期前缀 + 内容
    columns = ("content",)
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
    tree.heading("content", text="内容")
    tree.column("content", width=1000, anchor="w", stretch=True)
    tree.pack(fill="both", expand=True)
    scrollbar.config(command=tree.yview)

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        item = tree.item(selected[0])
        record_id = item["tags"][0] if item["tags"] else None
        if record_id and messagebox.askyesno("确认", "删除这条记录？"):
            time_delete(int(record_id))
            load_records()

    tree.bind("<Delete>", lambda e: delete_selected())

    def view_record(event=None):
        selected = tree.selection()
        if not selected:
            return
        item = tree.item(selected[0])
        record_id = item["tags"][0] if item["tags"] else None

        # 从 current_records 中按 id 找完整记录
        full_date = ""
        full_content = ""
        if record_id:
            for record in current_records:
                if str(record["id"]) == str(record_id):
                    full_date = record["date"]
                    full_content = record["content"]
                    break

        # 兜底：万一没找到，用表格显示值（至少能看到预览）
        if not full_content:
            values = item["values"]
            if values:
                fallback = values[0]
                if fallback.startswith("[") and "] " in fallback:
                    full_date = fallback[1:fallback.index("] ")]
                    full_content = fallback[fallback.index("] ") + 2:]
                else:
                    full_content = fallback

        view_win = tk.Toplevel(parent)
        view_win.title(full_date)
        view_win.configure(bg=COLORS["bg"])
        screen_width = view_win.winfo_screenwidth()
        screen_height = view_win.winfo_screenheight()
        win_width = min(800, int(screen_width * 0.8))
        win_height = min(600, int(screen_height * 0.8))
        view_win.geometry(f"{win_width}x{win_height}")
        view_win.resizable(True, True)
        view_win.update_idletasks()
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)
        view_win.geometry(f"{win_width}x{win_height}+{x}+{y}")

        tk.Label(view_win, text=full_date, bg=COLORS["bg"], fg="#666666", font=FONT_SMALL).pack(pady=10)

        content_frame = tk.Frame(view_win, bg=COLORS["bg"])
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(content_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(content_frame, font=FONT, bg=COLORS["bg"], fg=COLORS["text"],
                              relief="flat", wrap="word", yscrollcommand=scrollbar.set,
                              padx=10, pady=10)
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert("1.0", full_content)
        text_widget.config(state="disabled")

        tk.Button(view_win, text="关闭", command=view_win.destroy, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=2, takefocus=False).pack(pady=10)

    tree.bind("<Double-1>", view_record)

    tk.Button(filter_frame, text="删除选中", command=delete_selected, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left", padx=(5,0))

    tk.Button(filter_frame, text="查看", command=view_record, font=FONT_SMALL,
              relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
              activebackground=COLORS["active_bg"], cursor="hand2",
              highlightthickness=1, highlightbackground=COLORS["border"],
              padx=10, pady=2, takefocus=False).pack(side="left", padx=(5,0))

    def load_records():
        nonlocal current_records
        for item in tree.get_children():
            tree.delete(item)
        records = time_get_all()
        filtered = []
        for record in records:
            date = record["date"]
            content = record["content"]
            if filter_state["year"] and not date.startswith(filter_state["year"]):
                continue
            if filter_state["month"] and date[5:7] != filter_state["month"]:
                continue
            if filter_state["keyword"] and filter_state["keyword"] not in content.lower():
                continue
            filtered.append(record)
        filtered.sort(key=lambda x: x["date"], reverse=(filter_state["sort"] == "desc"))
        current_records = filtered
        if filter_state["keyword"]:
            search_info_label.config(text=f"找到 {len(filtered)} 条记录")
        else:
            search_info_label.config(text="")
        for record in filtered:
            content = record["content"]
            content_preview = content[:500] + "..." if len(content) > 500 else content
            display_text = f"[{record['date']}] {content_preview}"
            tree.insert("", "end", values=(display_text,), tags=(str(record["id"]),))

    def load_years():
        years = time_get_years()
        year_combo["values"] = ["全部年份"] + years

    load_years()
    load_records()

# ========== 存档页面 ==========
def create_archive_page(parent, back_callback):
    for widget in parent.winfo_children():
        widget.destroy()

    current_category = "当下"

    top_frame = tk.Frame(parent, bg=COLORS["bg"])
    top_frame.pack(fill="x", padx=10, pady=5)

    btn_back = tk.Button(top_frame, text="← 返回", command=back_callback, font=FONT_SMALL,
                         relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                         activebackground=COLORS["active_bg"], cursor="hand2",
                         highlightthickness=1, highlightbackground=COLORS["border"], padx=10, pady=2, takefocus=False)
    btn_back.pack(side="left")

    top_buttons_frame = tk.Frame(top_frame, bg=COLORS["bg"])
    top_buttons_frame.pack(side="left", padx=10)

    main_container = tk.Frame(parent, bg=COLORS["bg"])
    main_container.pack(fill="both", expand=True, padx=10, pady=5)

    def clear_top_buttons():
        for widget in top_buttons_frame.winfo_children():
            widget.destroy()

    def render_markdown(text_widget, content):
        text_widget.delete("1.0", tk.END)
        headings = []
        heading_counter = 0
        lines = content.split('\n')
        for line in lines:
            if line.startswith('### '):
                text = line[4:]
                heading_counter += 1
                tag = f"heading_{heading_counter}"
                text_widget.insert(tk.END, text + '\n', ("h3", tag))
                headings.append({"text": text, "level": 3, "tag": tag})
            elif line.startswith('## '):
                text = line[3:]
                heading_counter += 1
                tag = f"heading_{heading_counter}"
                text_widget.insert(tk.END, text + '\n', ("h2", tag))
                headings.append({"text": text, "level": 2, "tag": tag})
            elif line.startswith('# '):
                text = line[2:]
                heading_counter += 1
                tag = f"heading_{heading_counter}"
                text_widget.insert(tk.END, text + '\n', ("h1", tag))
                headings.append({"text": text, "level": 1, "tag": tag})
            elif line.startswith('> '):
                text_widget.insert(tk.END, line[2:] + '\n', "quote")
            elif line.strip() in ['---', '***', '___']:
                text_widget.insert(tk.END, '─' * 50 + '\n', "hr")
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                text_widget.insert(tk.END, '• ' + line.strip()[2:] + '\n')
            elif line.strip() == '':
                text_widget.insert(tk.END, '\n')
            else:
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        text_widget.insert(tk.END, part, "bold")
                    else:
                        text_widget.insert(tk.END, part)
                text_widget.insert(tk.END, '\n')
        return headings

    def show_list_view():
        for widget in main_container.winfo_children():
            widget.destroy()
        clear_top_buttons()
        btn_back.config(command=back_callback)

        tk.Button(top_buttons_frame, text="新建", command=show_edit_view_new, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=2, takefocus=False).pack(side="left", padx=(0,5))

        categories_frame = tk.Frame(main_container, bg=COLORS["bg"])
        categories_frame.pack(fill="x", pady=10)

        def switch_category(cat):
            nonlocal current_category
            current_category = cat
            show_list_view()

        for cat in NOTEBOOK_CATEGORIES:
            tk.Button(categories_frame, text=cat, command=lambda c=cat: switch_category(c),
                      font=FONT_SMALL, relief="flat", bd=0,
                      bg="#fff5f5" if cat == current_category else COLORS["bg"],
                      fg="#c25a5a" if cat == current_category else COLORS["text"],
                      activebackground=COLORS["active_bg"], cursor="hand2",
                      highlightthickness=1,
                      highlightbackground="#f5c6c6" if cat == current_category else COLORS["border"],
                      padx=10, pady=2, takefocus=False).pack(side="left", padx=(0,5))

        list_container = tk.Frame(main_container, bg=COLORS["bg"])
        list_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        articles = notebook_get_all()
        filtered = [a for a in articles if a["category"] == current_category]

        if not filtered:
            tk.Label(scrollable_frame, text="暂无文章", bg=COLORS["bg"], 
                    fg=COLORS["placeholder"], font=FONT).pack(pady=20)
        else:
            for article in filtered:
                title = article["title"] if article["title"] else "无标题"
                
                article_frame = tk.Frame(scrollable_frame, bg=COLORS["bg"])
                article_frame.pack(fill="x", pady=2, padx=20)
                
                title_label = tk.Label(
                    article_frame, 
                    text=title,
                    font=FONT,
                    bg=COLORS["bg"], 
                    fg=COLORS["text"],
                    cursor="hand2",
                    anchor="w",
                    wraplength=900,
                    justify="left",
                    pady=8
                )
                title_label.pack(fill="x")
                
                title_label.bind("<Button-1>", lambda e, a=article: show_view_view(a))
                title_label.bind("<Enter>", lambda e, label=title_label: label.config(bg="#fafafa"))
                title_label.bind("<Leave>", lambda e, label=title_label: label.config(bg=COLORS["bg"]))

    def show_view_view(article):
        for widget in main_container.winfo_children():
            widget.destroy()
        clear_top_buttons()
        btn_back.config(command=show_list_view)

        tk.Button(top_buttons_frame, text="编辑", command=lambda: show_edit_view_edit(article), font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=2, takefocus=False).pack(side="left", padx=(0,5))

        def delete_article():
            if messagebox.askyesno("确认", "确定删除这篇文章？"):
                notebook_delete(article["id"])
                show_list_view()

        tk.Button(top_buttons_frame, text="删除", command=delete_article, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=2, takefocus=False).pack(side="left")

        layout_frame = tk.Frame(main_container, bg=COLORS["bg"])
        layout_frame.pack(fill="both", expand=True)

        toc_frame = tk.Frame(layout_frame, bg=COLORS["bg"], width=220)
        toc_frame.pack(side="left", fill="y", padx=(0, 20))
        toc_frame.pack_propagate(False)

        content_frame = tk.Frame(layout_frame, bg=COLORS["bg"])
        content_frame.pack(side="left", fill="both", expand=True)

        title_label = tk.Label(
            content_frame, 
            text=article["title"] if article["title"] else "无标题",
            bg=COLORS["bg"], 
            fg="#c25a5a", 
            font=("微软雅黑", 20, "bold"),
            wraplength=900,
            justify="left", 
            anchor="w"
        )
        title_label.pack(fill="x", pady=(10, 20))

        content_scroll = tk.Frame(content_frame, bg=COLORS["bg"])
        content_scroll.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(content_scroll)
        scrollbar.pack(side="right", fill="y")

        content_text = tk.Text(content_scroll, font=FONT, bg=COLORS["bg"], fg=COLORS["text"],
                               relief="flat", wrap="word", yscrollcommand=scrollbar.set,
                               padx=20, pady=10, spacing1=3, spacing3=3)
        content_text.pack(fill="both", expand=True)
        scrollbar.config(command=content_text.yview)

        content_text.tag_config("h1", font=("微软雅黑", 20, "bold"), foreground="#c25a5a", spacing1=15, spacing3=10)
        content_text.tag_config("h2", font=("微软雅黑", 18, "bold"), foreground="#c25a5a", spacing1=12, spacing3=8)
        content_text.tag_config("h3", font=("微软雅黑", 16, "bold"), foreground=COLORS["text"], spacing1=10, spacing3=6)
        content_text.tag_config("quote", foreground="#555555", lmargin1=20, lmargin2=20, spacing1=8, spacing3=8)
        content_text.tag_config("code", font=("Courier New", 11), background="#f5f5f5", lmargin1=15, lmargin2=15, spacing1=5, spacing3=5)
        content_text.tag_config("hr", foreground="#dddddd", spacing1=10, spacing3=10)
        content_text.tag_config("bold", font=("微软雅黑", 12, "bold"))

        all_headings = render_markdown(content_text, article["content"])
        toc_headings = [h for h in all_headings if h["level"] <= 2]

        if toc_headings:
            tk.Label(toc_frame, text="目录", bg=COLORS["bg"], fg="#555555", font=("微软雅黑", 13, "bold")).pack(anchor="w", pady=(10, 8))
            for heading in toc_headings:
                indent = 0 if heading["level"] == 1 else 15
                tk.Label(toc_frame, text=heading["text"],
                         bg=COLORS["bg"],
                         fg="#555555" if heading["level"] == 1 else "#777777",
                         font=("微软雅黑", 11 if heading["level"] == 1 else 10),
                         anchor="w", padx=indent, pady=3,
                         wraplength=180, justify="left").pack(fill="x")
        else:
            tk.Label(toc_frame, text="无目录", bg=COLORS["bg"], fg="#bbbbbb", font=FONT_SMALL).pack(anchor="w", pady=(10, 8))

        float_frame = tk.Frame(main_container, bg=COLORS["bg"])
        float_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        def scroll_to_top():
            content_text.see("1.0")
            content_text.focus()

        def scroll_to_bottom():
            content_text.see(tk.END)
            content_text.focus()

        tk.Button(float_frame, text="↑", command=scroll_to_top, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  width=2, pady=2, takefocus=False).pack(side="left", padx=2)

        tk.Button(float_frame, text="↓", command=scroll_to_bottom, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  width=2, pady=2, takefocus=False).pack(side="left", padx=2)

    def show_edit_view_new():
        show_edit_view(None)

    def show_edit_view_edit(article):
        show_edit_view(article)

    def show_edit_view(article):
        for widget in main_container.winfo_children():
            widget.destroy()
        clear_top_buttons()
        btn_back.config(command=show_list_view)

        def save_article():
            title = title_entry.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            category = category_var.get()
            if not content:
                messagebox.showwarning("提示", "内容不能为空")
                return
            if article and article["id"]:
                notebook_update(article["id"], title, content, category)
            else:
                notebook_add(title, content, category)
            show_list_view()

        tk.Button(top_buttons_frame, text="保存", command=save_article, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=15, pady=2, takefocus=False).pack(side="left")

        edit_container = tk.Frame(main_container, bg=COLORS["bg"])
        edit_container.pack(fill="both", expand=True)

        edit_center = tk.Frame(edit_container, bg=COLORS["bg"], width=800)
        edit_center.pack(anchor="center", fill="both", expand=True, padx=50)

        tk.Label(edit_center, text="标题", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL).pack(anchor="w", pady=(10, 5))
        title_entry = tk.Entry(edit_center, font=FONT, relief="solid", bd=1)
        title_entry.pack(fill="x", pady=(0, 10))
        if article and article["title"]:
            title_entry.insert(0, article["title"])

        tk.Label(edit_center, text="分类", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL).pack(anchor="w", pady=(0, 5))
        category_var = tk.StringVar(value=article["category"] if article else "当下")
        category_combo = ttk.Combobox(edit_center, textvariable=category_var, values=NOTEBOOK_CATEGORIES, font=FONT, state="readonly")
        category_combo.pack(fill="x", pady=(0, 10))

        tk.Label(edit_center, text="内容（支持Markdown）", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_SMALL).pack(anchor="w", pady=(0, 5))

        content_frame = tk.Frame(edit_center, bg=COLORS["bg"])
        content_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(content_frame)
        scrollbar.pack(side="right", fill="y")

        content_text = tk.Text(content_frame, font=FONT, bg=COLORS["bg"], fg=COLORS["text"],
                               relief="solid", bd=1, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10)
        content_text.pack(fill="both", expand=True)
        scrollbar.config(command=content_text.yview)

        if article and article["content"]:
            content_text.insert("1.0", article["content"])

    show_list_view()

# ========== 数据库查看器页面 ==========
def create_db_viewer_page(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    left_frame = tk.Frame(parent, bg=COLORS["bg"], width=200)
    left_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
    left_frame.pack_propagate(False)

    tk.Label(left_frame, text="数据库表", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITLE).pack(anchor="w", pady=(0, 10))

    tables = db_get_tables()
    table_buttons = {}

    right_frame = tk.Frame(parent, bg=COLORS["bg"])
    right_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

    def update_table_buttons(selected_table=None):
        for name, btn in table_buttons.items():
            if name == selected_table:
                btn.config(
                    bg="#fff5f5",
                    fg="#c25a5a",
                    highlightbackground="#f5c6c6",
                    activebackground="#ffe0e0"
                )
            else:
                btn.config(
                    bg=COLORS["button_bg"],
                    fg=COLORS["button_fg"],
                    highlightbackground=COLORS["border"],
                    activebackground=COLORS["active_bg"]
                )

    def show_table_data(table_name, page=1):
        for widget in right_frame.winfo_children():
            widget.destroy()
        
        update_table_buttons(table_name)
        
        limit = 500
        offset = (page - 1) * limit
        columns, records = db_get_table_data(table_name, offset, limit)
        total = db_get_table_count(table_name)
        total_pages = max(1, (total + limit - 1) // limit)
        
        info_frame = tk.Frame(right_frame, bg=COLORS["bg"])
        info_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(info_frame, text=f"表：{table_name}", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITLE).pack(side="left")
        tk.Label(info_frame, text=f"（共 {total} 条记录，第 {page}/{total_pages} 页）", bg=COLORS["bg"], fg="#888888", font=FONT_SMALL).pack(side="left", padx=(10, 0))
        
        page_frame = tk.Frame(info_frame, bg=COLORS["bg"])
        page_frame.pack(side="right")
        
        def go_prev():
            if page > 1:
                show_table_data(table_name, page - 1)
        
        def go_next():
            if page < total_pages:
                show_table_data(table_name, page + 1)
        
        tk.Button(page_frame, text="上一页", command=go_prev, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=10, pady=2, takefocus=False).pack(side="left", padx=(0, 5))
        
        tk.Button(page_frame, text="下一页", command=go_next, font=FONT_SMALL,
                  relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], cursor="hand2",
                  highlightthickness=1, highlightbackground=COLORS["border"],
                  padx=10, pady=2, takefocus=False).pack(side="left")
        
        table_frame = tk.Frame(right_frame, bg=COLORS["bg"])
        table_frame.pack(fill="both", expand=True)
        
        h_scrollbar = tk.Scrollbar(table_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        v_scrollbar = tk.Scrollbar(table_frame)
        v_scrollbar.pack(side="right", fill="y")
        
        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        
        tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                           yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="w")
        
        tree.pack(fill="both", expand=True)
        v_scrollbar.config(command=tree.yview)
        h_scrollbar.config(command=tree.xview)
        
        for record in records:
            values = [record[col] if record[col] is not None else "" for col in columns]
            tree.insert("", "end", values=values)
        
        def on_double_click(event):
            region = tree.identify("region", event.x, event.y)
            if region != "cell":
                return
            column = tree.identify_column(event.x)
            row_id = tree.identify_row(event.y)
            if not row_id:
                return
            col_index = int(column.replace("#", "")) - 1
            col_name = columns[col_index]
            item = tree.item(row_id)
            values = item["values"]
            full_text = values[col_index]
            
            top = tk.Toplevel(parent)
            top.title(f"{col_name} 完整内容")
            top.configure(bg=COLORS["bg"])
            top.geometry("600x400")
            text_widget = tk.Text(top, font=("微软雅黑", 11), wrap="word", padx=10, pady=10)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", str(full_text))
            text_widget.config(state="disabled")
            tk.Button(top, text="关闭", command=top.destroy, font=FONT_SMALL,
                      relief="flat", bd=0, bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                      activebackground=COLORS["active_bg"], cursor="hand2",
                      highlightthickness=1, highlightbackground=COLORS["border"],
                      padx=15, pady=2, takefocus=False).pack(pady=10)
        
        tree.bind("<Double-1>", on_double_click)

    for table_name in tables:
        btn = tk.Button(left_frame, text=table_name,
                        command=lambda t=table_name: show_table_data(t),
                        font=FONT_SMALL, relief="flat", bd=0,
                        bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                        activebackground=COLORS["active_bg"], cursor="hand2",
                        highlightthickness=1, highlightbackground=COLORS["border"],
                        padx=10, pady=5, anchor="w", takefocus=False)
        btn.pack(fill="x", pady=2)
        table_buttons[table_name] = btn

    tk.Label(right_frame, text="← 点击左侧表名查看数据", bg=COLORS["bg"], 
             fg=COLORS["placeholder"], font=FONT).pack(expand=True)

# ========== 主窗口 ==========
def create_main_window():
    global root
    root = tk.Tk()
    root.withdraw()                                     # === 先隐藏 ===
    try:
        root.iconbitmap(resource_path("myicon.ico"))
    except Exception:
        pass
    root.title("benj笔记本")
    root.configure(bg=COLORS["bg"])
    root.resizable(True, True)

    # === 直接算出屏幕大小，一次性设好，避免"小窗→撑大" ===
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{screen_w}x{screen_h}+0+0")

    main_notebook = ttk.Notebook(root)
    main_notebook.pack(fill="both", expand=True)

    tab_blog = tk.Frame(main_notebook, bg=COLORS["bg"])
    main_notebook.add(tab_blog, text="博客")

    tab_db = tk.Frame(main_notebook, bg=COLORS["bg"])
    main_notebook.add(tab_db, text="数据库")

    def show_money():
        for widget in tab_blog.winfo_children():
            widget.destroy()
        create_money_page(tab_blog, show_main_menu)

    def show_time():
        for widget in tab_blog.winfo_children():
            widget.destroy()
        create_time_page(tab_blog, show_main_menu)

    def show_archive():
        for widget in tab_blog.winfo_children():
            widget.destroy()
        create_archive_page(tab_blog, show_main_menu)

    def show_main_menu():
        for widget in tab_blog.winfo_children():
            widget.destroy()
        create_main_menu()

    def create_main_menu():
        container = tk.Frame(tab_blog, bg=COLORS["bg"])
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(container, text="钱", command=show_money, width=20, height=2,
                  font=FONT_TITLE, relief="flat", bd=0,
                  bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], activeforeground=COLORS["button_fg"],
                  cursor="hand2", highlightthickness=1,
                  highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                  takefocus=False).pack(pady=10)

        tk.Button(container, text="时间", command=show_time, width=20, height=2,
                  font=FONT_TITLE, relief="flat", bd=0,
                  bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], activeforeground=COLORS["button_fg"],
                  cursor="hand2", highlightthickness=1,
                  highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                  takefocus=False).pack(pady=10)

        tk.Button(container, text="存档", command=show_archive, width=20, height=2,
                  font=FONT_TITLE, relief="flat", bd=0,
                  bg=COLORS["button_bg"], fg=COLORS["button_fg"],
                  activebackground=COLORS["active_bg"], activeforeground=COLORS["button_fg"],
                  cursor="hand2", highlightthickness=1,
                  highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
                  takefocus=False).pack(pady=10)

    create_main_menu()
    create_db_viewer_page(tab_db)

    root.deiconify()                                    # === 全部搭完再一次性显示 ===
    root.mainloop()

def main():
    init_db()
    pin_verify_window()

if __name__ == "__main__":
    main()