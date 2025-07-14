import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# ⚠️ NHỚ thay ID bên dưới bằng ID của bạn (dòng in phía dưới sẽ giúp bạn biết ID của mình)
ALLOWED_ADMINS = ["1014803363105349693"]  # Thêm nhiều ID nếu cần

class AddMoney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip()
        content_lower = content.lower()

        # In ID của người gửi để bạn biết ID của chính mình
        print(f"[LOG] Message from: {message.author} (ID: {message.author.id})")

        if not (content_lower.startswith("haddmoney") or content_lower.startswith("h addmoney")):
            return

        author_id = str(message.author.id)
        if author_id not in ALLOWED_ADMINS:
            await message.channel.send("❌ Bạn không có quyền dùng lệnh này.")
            return

        words = content.split()
        print(f"[LOG] Command words: {words}")

        # Tìm số tiền
        amount = None
        for i, word in enumerate(words):
            if word.lower() == "addmoney" or word.lower().startswith("haddmoney"):
                try:
                    amount = int(words[i + 1])
                    break
                except IndexError:
                    await message.channel.send("❌ Thiếu số tiền.")
                    return
                except ValueError:
                    await message.channel.send("❌ Số tiền không hợp lệ.")
                    return

        if amount is None or amount <= 0:
            await message.channel.send("❌ Số tiền phải lớn hơn 0.")
            return

        if not message.mentions:
            await message.channel.send("❌ Bạn cần tag người nhận (dạng: @username).")
            return

        target_user = message.mentions[0]
        target_id = str(target_user.id)

        # Xử lý cộng tiền
        c.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
        row = c.fetchone()
        if row:
            balance = row[0] + amount
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, target_id))
        else:
            balance = 1000 + amount
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                      (target_id, target_user.name, balance))

        conn.commit()

        await message.channel.send(
            f"✅ Đã thêm **{amount}** 💰 cho {target_user.mention}!\n💳 Số dư mới: **{balance}**"
        )

# Setup
async def setup(bot):
    await bot.add_cog(AddMoney(bot))
