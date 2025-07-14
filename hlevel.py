import discord
from discord.ext import commands
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont
import io
import time
import aiohttp

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Đảm bảo có bảng và các cột cần thiết
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    last_xp_time REAL DEFAULT 0
)
""")
conn.commit()

class HLevel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def generate_level_image(self, member: discord.Member, level: int, xp: int, required_xp: int, rank: int):
        WIDTH, HEIGHT = 934, 282
        bar_width = 615
        avatar_size = 190

        # Load nền từ file hoặc màu nền đơn giản
        background = Image.new("RGB", (WIDTH, HEIGHT), color=(30, 33, 36))
        draw = ImageDraw.Draw(background)

        # Font
        font_title = ImageFont.truetype("arial.ttf", 32)
        font_label = ImageFont.truetype("arial.ttf", 20)
        font_xp = ImageFont.truetype("arial.ttf", 24)
        font_rank = ImageFont.truetype("arial.ttf", 22)

        # Ảnh avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.avatar.url)) as resp:
                avatar_bytes = await resp.read()

        avatar_img = Image.open(io.BytesIO(avatar_bytes)).resize((avatar_size, avatar_size)).convert("RGBA")
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
        background.paste(avatar_img, (40, 46), mask=mask)

        # Text
        draw.text((260, 50), member.name, font=font_title, fill=(255, 255, 255))
        draw.text((260, 95), "UwU Bot User", font=font_label, fill=(170, 170, 170))
        draw.text((260, 140), f"XP: {xp} / {required_xp}", font=font_xp, fill=(255, 255, 255))
        draw.text((760, 80), f"LVL {level}", font=font_xp, fill=(255, 255, 255))
        draw.text((760, 110), f"RANK #{rank}", font=font_rank, fill=(255, 215, 0))

        # Thanh XP
        percent = xp / required_xp
        bar_height = 24
        bar_x, bar_y = 260, 180
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(80, 80, 80))
        draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * percent), bar_y + bar_height], fill=(0, 255, 255))

        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        username = message.author.name
        now = time.time()

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

        content = message.content.lower().strip()
        if content.startswith("hlevel") or content.startswith("h level"):
            required_xp = level * 100
            # Tính rank trong server
            c.execute("SELECT user_id FROM users ORDER BY level DESC, xp DESC")
            all_users = c.fetchall()
            rank = next((i + 1 for i, (uid,) in enumerate(all_users) if uid == user_id), -1)

            image = await self.generate_level_image(message.author, level, xp, required_xp, rank)
            file = discord.File(image, filename="level.png")
            await message.channel.send(file=file)

    @commands.command(name="hlb")
    async def leaderboard(self, ctx):
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
