import discord
from discord.ext import commands
import sqlite3

# Kết nối DB
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Đảm bảo bảng có đủ cột
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 1000,
        bank_balance INTEGER DEFAULT 0,
        last_daily REAL DEFAULT 0,
        level INTEGER DEFAULT 1,
        married_to TEXT DEFAULT NULL,
        profile_frame INTEGER DEFAULT NULL
    )
''')
conn.commit()

PROFILE_FRAMES = {
    401: {"name": "Blue Frame", "emoji": "🔵"},
    402: {"name": "Red Frame", "emoji": "🔴"},
    403: {"name": "Purple Frame", "emoji": "🟣"},
}

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if content.startswith("hprofile set frame") or content.startswith("h profile set frame"):
            args = content.split()
            if len(args) < 4:
                await message.channel.send("❌ Dùng đúng cú pháp: `hprofile set frame <id>`")
                return
            try:
                frame_id = int(args[3])
                if frame_id not in PROFILE_FRAMES:
                    await message.channel.send("❌ ID khung không hợp lệ.")
                    return
                user_id = str(message.author.id)
                c.execute("UPDATE users SET profile_frame = ? WHERE user_id = ?", (frame_id, user_id))
                conn.commit()
                await message.channel.send(f"✅ Đã trang bị khung: {PROFILE_FRAMES[frame_id]['emoji']} {PROFILE_FRAMES[frame_id]['name']}")
                return
            except ValueError:
                await message.channel.send("❌ ID phải là số.")
                return

        if not (content.startswith("hprofile") or content.startswith("h profile")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Truy vấn user
        c.execute("SELECT balance, level, married_to, profile_frame FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if not row:
            await message.channel.send("❌ Hồ sơ của bạn chưa tồn tại.")
            return

        balance, level, married_to, profile_frame = row
        spouse = f"<@{married_to}>" if married_to else "Chưa kết hôn"

        frame_emoji = PROFILE_FRAMES.get(profile_frame, {}).get("emoji", "📘")
        frame_name = PROFILE_FRAMES.get(profile_frame, {}).get("name", "Không có")

        embed = discord.Embed(
            title=f"{frame_emoji} Hồ sơ của {username}",
            color=0x00FF00
        )
        embed.add_field(name="💰 Số dư", value=f"{balance}", inline=True)
        embed.add_field(name="🏆 Level", value=str(level), inline=True)
        embed.add_field(name="💍 Đã kết hôn với", value=spouse, inline=True)
        embed.add_field(name="🖼️ Khung hồ sơ", value=f"{frame_name}", inline=True)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text="❤️ Còn độc thân thì còn cơ hội!")

        await message.channel.send(embed=embed)

# Setup Cog
async def setup(bot):
    await bot.add_cog(Profile(bot))
