import sqlite3
import os

# Xóa cơ sở dữ liệu cũ nếu có
if os.path.exists("users.db"):
    os.remove("users.db")
    print("⚠️ Đã xóa cơ sở dữ liệu cũ.")

# Tạo lại cơ sở dữ liệu mới
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tạo bảng 'users' mới với cột 'claimed_reward'
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    bank_balance INTEGER DEFAULT 0,
    last_daily REAL DEFAULT 0,
    level INTEGER DEFAULT 1,
    married_to TEXT DEFAULT NULL,
    profile_frame INTEGER DEFAULT NULL,
    claimed_reward INTEGER DEFAULT 0  -- Thêm cột claimed_reward
)
''')

# Cam kết thay đổi và đóng kết nối
conn.commit()
conn.close()

print("✅ Đã tạo lại cơ sở dữ liệu và bảng 'users' với cột 'claimed_reward'.")


import sqlite3

# Kết nối đến cơ sở dữ liệu
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Kiểm tra bảng 'users' có tồn tại không
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
if c.fetchone() is None:
    print("⚠️ Bảng 'users' không tồn tại.")
else:
    print("✅ Bảng 'users' tồn tại, kiểm tra các cột...")

# Kiểm tra cột claimed_reward
c.execute('PRAGMA table_info(users);')
columns = [column[1] for column in c.fetchall()]
if 'claimed_reward' in columns:
    print("✅ Cột 'claimed_reward' đã tồn tại trong bảng 'users'.")
else:
    print("⚠️ Cột 'claimed_reward' không có trong bảng 'users'.")

# Đóng kết nối
conn.close()
