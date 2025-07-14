import discord
from discord.ext import commands
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import io
import time

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tạo bảng users nếu chưa có
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000
)
''')

# Các cột mở rộng cho bảng users (đã thêm profile_frame)
columns = [
    ("last_daily", "REAL DEFAULT 0"),
    ("bank_balance", "INTEGER DEFAULT 0"),
    ("level", "INTEGER DEFAULT 1"),
    ("married_to", "TEXT DEFAULT NULL"),
    ("claimed_reward", "INTEGER DEFAULT 0"),
    ("xp", "INTEGER DEFAULT 0"),
    ("last_xp_time", "REAL DEFAULT 0"),
    ("profile_frame", "INTEGER DEFAULT NULL")  # ✅ thêm cột profile_frame
]

for column_name, definition in columns:
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {column_name} {definition}")
        print(f"✅ Đã thêm '{column_name}'")
    except sqlite3.OperationalError as e:
        print(f"⚠️ '{column_name}' có thể đã tồn tại:", e)

# ✅ Tạo bảng inventory nếu chưa có
try:
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT,
            item_key TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_key)
        )
    ''')
    print("✅ Đã tạo bảng 'inventory'")
except Exception as e:
    print("❌ Lỗi tạo bảng inventory:", e)

conn.commit()
conn.close()

class HLevel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_level_image(self, username, level, xp, required_xp):
        img = Image.new("RGB", (500, 150), color=(54, 57, 63))
        draw = ImageDraw.Draw(img)

        font_title = ImageFont.load_default()
        font_content = ImageFont.load_default()

        draw.text((20, 20), f"{username}'s Level", font=font_title, fill=(255, 255, 255))
        draw.text((20, 60), f"Level: {level}", font=font_content, fill=(255, 255, 0))
        draw.text((20, 85), f"XP: {xp} / {required_xp}", font=font_content, fill=(255, 255, 255))

        # Thanh tiến trình XP
        bar_x = 20
        bar_y = 120
        bar_width = 460
        bar_height = 15
        progress = int((xp / required_xp) * bar_width)

        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(100, 100, 100))
        draw.rectangle([bar_x, bar_y, bar_x + progress, bar_y + bar_height], fill=(0, 255, 0))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        username = message.author.name
        now = time.time()

        c = conn.cursor()
        c.execute("SELECT xp, level, balance, last_xp_time FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if not row:
            c.execute("INSERT INTO users (user_id, username, balance, level, xp, last_xp_time) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, username, 1000, 1, 0, now))
            conn.commit()
            xp = 0
            level = 1
            balance = 1000
            last_xp_time = 0
        else:
            xp, level, balance, last_xp_time = row

        # Cooldown: 60 giây
        if now - last_xp_time >= 60:
            xp += 10
            level_up = False
            required_xp = level * 100
            if xp >= required_xp:
                level += 1
                xp -= required_xp
                level_up = True
                reward = random.randint(100, 300)
                balance += reward
                await message.channel.send(f"🎉 {message.author.mention} đã lên cấp **{level}** và nhận được 💰 {reward} coin!")

            c.execute("UPDATE users SET xp = ?, level = ?, balance = ?, last_xp_time = ? WHERE user_id = ?",
                      (xp, level, balance, now, user_id))
            conn.commit()

        # Lệnh hiển thị level bằng ảnh
        content = message.content.lower().strip()
        if content.startswith("hlevel") or content.startswith("h level"):
            required_xp = level * 100
            image = self.generate_level_image(username, level, xp, required_xp)
            file = discord.File(image, filename="level.png")
            await message.channel.send(file=file)

    @commands.command(name="hlb")
    async def leaderboard(self, ctx):
        c = conn.cursor()
        c.execute("SELECT username, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT 10")
        rows = c.fetchall()

        embed = discord.Embed(
            title="🏆 Bảng xếp hạng cấp độ",
            color=0xf1c40f
        )

        for i, (username, level, xp) in enumerate(rows, start=1):
            embed.add_field(
                name=f"#{i} {username}",
                value=f"Level: {level} | XP: {xp}",
                inline=False
            )

        await ctx.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(HLevel(bot))
