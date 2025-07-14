import discord
from discord.ext import commands
import sqlite3
import random
import asyncio
import time  # Thư viện time để quản lý cooldown
import os
import datetime  # Thêm thư viện datetime để sử dụng giờ

# Lưu cooldown của từng user
user_cooldowns = {}  # user_id: timestamp

GIF_LINKS = {
    "flipping": "https://media.tenor.com/UTgK0rCiKLMAAAAi/ultimate-coin-flip-lucky-louie-flip.gif",
    "head": "https://i.imgur.com/hOidl0u.png",
    "tails": "https://i.imgur.com/Z2lHqjq.png"
}

# Kiểm tra xem file đã tồn tại chưa và xóa nó nếu có
if os.path.exists("users.db"):
    os.remove("users.db")

# Tạo lại file users.db
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tạo bảng users nếu chưa tồn tại và đảm bảo có cột last_daily, bank_balance
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    bank_balance INTEGER DEFAULT 0,
    last_daily REAL DEFAULT 0,
    level INTEGER DEFAULT 1,
    married_to TEXT DEFAULT NULL
)
''')
conn.commit()

# Khởi tạo bot và intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ⚠️ NHỚ thay ID bên dưới bằng ID của bạn
ALLOWED_ADMINS = ["1014803363105349693"]  # Thêm nhiều ID nếu cần

# Format tiền
def format_money(amount):
    return "{:,}".format(amount)

# Cog Cash
class Cash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not (content.startswith("hcash") or content.startswith("h cash")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy hoặc tạo user
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if row:
            balance = row[0]
        else:
            balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                      (user_id, username, balance))
            conn.commit()

        # Lấy giờ hiện tại theo giờ Việt Nam (UTC+7)
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        current_time = now.strftime('%H:%M:%S')

        # Tạo embed đẹp với các hiệu ứng
        embed = discord.Embed(
            description=f"💳 **| {message.author.mention}**, bạn hiện đang có\n**<:cowoncy:416043450337853441> ```{format_money(balance)} cowoncy```**",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Số dư tài khoản", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="💼 Kiểm tra tiền xài chơi thôi 😎", icon_url="https://youriconlink.com/icon.png")
        embed.set_thumbnail(url="https://youriconlink.com/thumbnail.png")
        embed.add_field(name="💬 Thời gian kiểm tra:", value=f"```{current_time}```", inline=False)
        
        # Thêm dấu "!" vào sau thông báo
        embed.add_field(name="🎯 Dùng cowoncy cho các hoạt động", value="Chơi game, vote, tặng quà... !", inline=False)
        embed.add_field(name="💡 Cách kiếm cowoncy", value="Làm quest, vote cho bot, tham gia các sự kiện!", inline=False)

        # Để đẹp hơn nữa, có thể thêm nền hoặc hình ảnh.
        embed.set_image(url="https://yourbackgroundimage.com/image.png") 

        await message.channel.send(embed=embed)

# Cog Daily
class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Các định dạng chấp nhận: hdaily, Hdaily, h daily, H daily
        if not (content.startswith("hdaily") or content.startswith("h daily")):
            return

        user_id = str(message.author.id)
        username = message.author.name
        now = time.time()
        cooldown_seconds = 24 * 60 * 60  # 24 giờ

        # Lấy hoặc tạo user
        c.execute("SELECT balance, last_daily FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance, last_daily = row
        else:
            balance = 1000
            last_daily = 0
            c.execute("INSERT INTO users (user_id, username, balance, last_daily) VALUES (?, ?, ?, ?)", (user_id, username, balance, last_daily))
            conn.commit()

        # Kiểm tra cooldown
        if now - last_daily < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_daily))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await message.channel.send(f"⏳ Bạn cần chờ **{hours} giờ {minutes} phút** để nhận quà daily tiếp theo.")
            return

        # Cập nhật thưởng
        reward = random.randint(50, 150)
        balance += reward
        last_daily = now
        c.execute("UPDATE users SET balance = ?, last_daily = ? WHERE user_id = ?", (balance, last_daily, user_id))
        conn.commit()

        # Gửi embed kết quả
        embed = discord.Embed(
            title=f"{username} đã nhận daily 💰",
            description=f"> Bạn nhận được: **{reward}** coin!",
            color=0x00FF00
        )
        embed.add_field(name="💳 Số dư hiện tại", value=f"{balance}", inline=True)
        embed.set_footer(text="Hãy quay lại sau 24 giờ để nhận tiếp!")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)
 
# Cog AddMoney
class AddMoney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip()
        content_lower = content.lower()

        if not (content_lower.startswith("haddmoney") or content_lower.startswith("h addmoney")):
            return

        author_id = str(message.author.id)
        if author_id not in ALLOWED_ADMINS:
            await message.channel.send("❌ Bạn không có quyền dùng lệnh này.")
            return

        words = content.split()

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

# Cog Coinflip
class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        if not content.startswith("h"):
            return

        content = content[1:].strip()

        if content.startswith("cf"):
            content = content[2:].strip()
        elif content.startswith(" cf"):
            content = content[3:].strip()
        else:
            return

        bet_arg = content.replace(" ", "")
        if not bet_arg:
            await message.channel.send("❌ Bạn chưa nhập số tiền cược.")
            return

        user_id = str(message.author.id)
        username = message.author.name

        # ===== KIỂM TRA COOLDOWN =====
        now = time.time()
        last_play = user_cooldowns.get(user_id, 0)
        cooldown_seconds = 15

        if now - last_play < cooldown_seconds:
            wait_time = int(cooldown_seconds - (now - last_play))
            await message.channel.send(f"🕒 Vui lòng chờ **{wait_time} giây** trước khi chơi lại.")
            return

        # Truy vấn DB
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance = row[0]
        else:
            balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, username, balance))
            conn.commit()

        # Xử lý số tiền
        if bet_arg == "all":
            bet = balance
        else:
            try:
                bet = int(bet_arg)
            except ValueError:
                await message.channel.send("❌ Số tiền cược không hợp lệ.")
                return

        if bet <= 0:
            await message.channel.send("❌ Số tiền phải lớn hơn 0.")
            return

        if bet > balance:
            await message.channel.send("💸 Bạn không đủ tiền để cược.")
            return

        # ===== CẬP NHẬT THỜI GIAN CHƠI =====
        user_cooldowns[user_id] = time.time()

        # Random mặt coin
        choice = random.choice(["head", "tails"])
        result = random.choice(["head", "tails"])
        win = result == choice
        reward = bet * 2 if win else 0
        balance += reward if win else -bet

        # Embed flipping
        flipping_embed = discord.Embed(description=f"🪙 Coin is flipping... (Bạn chọn ngẫu nhiên: **{choice}**)", color=0xFFFF00)
        flipping_embed.set_thumbnail(url=GIF_LINKS["flipping"])
        flipping_msg = await message.channel.send(embed=flipping_embed)
        await asyncio.sleep(3)

        # Cập nhật DB
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
        conn.commit()

        # Kết quả
        result_embed = discord.Embed(
            title=f"You {'Won' if win else 'Lost'}!",
            description=f"> Kết quả: `{result}`\n> Bạn chọn: `{choice}`\n\nBạn {'nhận' if win else 'mất'} 💰 {reward if win else -bet}",
            color=0x00FF00 if win else 0xFF0000
        )
        result_embed.set_thumbnail(url=GIF_LINKS[result])
        result_embed.add_field(name="💳 Số dư còn lại", value=f"{balance}", inline=True)
        result_embed.timestamp = message.created_at
        await flipping_msg.edit(embed=result_embed)

# Cog Bank
class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Nhận các dạng: hbank, Hbank, h bank, H bank
        if not (content.startswith("hbank") or content.startswith("h bank")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy hoặc tạo user
        c.execute("SELECT balance, bank_balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance, bank_balance = row
        else:
            balance = 1000
            bank_balance = 0
            c.execute("INSERT INTO users (user_id, username, balance, bank_balance) VALUES (?, ?, ?, ?)",
                      (user_id, username, balance, bank_balance))
            conn.commit()

        # Gửi embed hiển thị số dư
        embed = discord.Embed(title="🏦 Bank Balance", color=0x00FF00)
        embed.add_field(name="💰 Ví", value=f"{balance}", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"{bank_balance}", inline=True)
        embed.set_footer(text="Dùng lệnh gửi/rút để chuyển tiền giữa ví và ngân hàng.")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Cog Give
class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content.lower().startswith(("hgive", "h give")):
            return

        parts = message.content.strip().split()
        if len(parts) < 3:
            await message.channel.send("❌ Cú pháp: `hgive @user <số tiền>`")
            return

        try:
            recipient = message.mentions[0]
        except IndexError:
            await message.channel.send("❌ Bạn phải **tag** người nhận tiền.")
            return

        try:
            amount = int(parts[-1])
        except ValueError:
            await message.channel.send("❌ Số tiền không hợp lệ.")
            return

        if amount <= 0:
            await message.channel.send("❌ Số tiền phải lớn hơn 0.")
            return

        sender_id = str(message.author.id)
        recipient_id = str(recipient.id)

        if sender_id == recipient_id:
            await message.channel.send("❌ Không thể gửi tiền cho chính bạn.")
            return

        # Lấy hoặc tạo người gửi
        c.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
        sender_data = c.fetchone()
        if not sender_data:
            await message.channel.send("❌ Bạn chưa có tài khoản.")
            return

        sender_balance = sender_data[0]
        if sender_balance < amount:
            await message.channel.send("💸 Bạn không đủ tiền để gửi.")
            return

        # Lấy hoặc tạo người nhận
        c.execute("SELECT balance FROM users WHERE user_id = ?", (recipient_id,))
        recipient_data = c.fetchone()
        if recipient_data:
            recipient_balance = recipient_data[0]
        else:
            recipient_balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                      (recipient_id, recipient.name, recipient_balance))

        # Giao dịch
        sender_balance -= amount
        recipient_balance += amount

        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (sender_balance, sender_id))
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (recipient_balance, recipient_id))
        conn.commit()

        await message.channel.send(
            f"✅ {message.author.mention} đã gửi **{amount}** 💰 cho {recipient.mention}.\n"
            f"📤 Số dư còn lại: **{sender_balance}**"
        )

     # Định nghĩa bộ bài (sử dụng điểm, không cần suit)
deck_values = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10
}
deck_cards = list(deck_values.keys())

active_games = {}  # Lưu ván chơi theo user_id

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def draw_card(self):
        return random.choice(deck_cards)

    def calculate_points(self, hand):
        points = sum(deck_values[card] for card in hand)
        # Hạ A từ 11 xuống 1 nếu cần
        aces = hand.count("A")
        while points > 21 and aces:
            points -= 10
            aces -= 1
        return points

    async def end_game(self, user_id):
        if user_id in active_games:
            del active_games[user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if not (content.startswith("hbj") or content.startswith("h bj") or content.startswith("h bj") or content.startswith("Hbj")):
            return

        user_id = message.author.id
        if user_id in active_games:
            await message.channel.send("🚫 Bạn đang chơi 1 ván rồi! Kết thúc trước khi chơi tiếp.")
            return

        # Khởi tạo ván chơi
        player_hand = [self.draw_card(), self.draw_card()]
        dealer_hand = [self.draw_card(), self.draw_card()]

        active_games[user_id] = {
            "player": player_hand,
            "dealer": dealer_hand,
            "message": None
        }

        await self.show_game(message.channel, message.author)

    async def show_game(self, channel, user):
        game = active_games[user.id]
        player = game["player"]
        dealer = game["dealer"]

        player_points = self.calculate_points(player)
        dealer_display = dealer[0] + ", ❓"

        embed = discord.Embed(
            title=f"🃏 Blackjack - {user.display_name}",
            description=(
                f"**Bài của bạn:** {', '.join(player)} (Tổng: {player_points})\n"
                f"**Bài của Dealer:** {dealer_display}\n\n"
                "👊 để **rút bài** | 🛑 để **dừng**"
            ),
            color=0x00ff99
        )

        sent_msg = await channel.send(embed=embed)
        game["message"] = sent_msg

        await sent_msg.add_reaction("👊")
        await sent_msg.add_reaction("🛑")

        def check(reaction, user_check):
            return (
                user_check.id == user.id and
                str(reaction.emoji) in ["👊", "🛑"] and
                reaction.message.id == sent_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "👊":
                await self.hit(user, channel)
            else:
                await self.stand(user, channel)
        except:
            await channel.send("⏱️ Hết giờ. Ván chơi kết thúc.")
            await self.end_game(user.id)

    async def hit(self, user, channel):
        game = active_games[user.id]
        game["player"].append(self.draw_card())

        if self.calculate_points(game["player"]) > 21:
            await channel.send(f"💥 **{user.mention} BÙM! Quá 21 điểm! Bạn thua rồi.**")
            await self.end_game(user.id)
        else:
            await self.show_game(channel, user)

    async def stand(self, user, channel):
        game = active_games[user.id]
        player_score = self.calculate_points(game["player"])
        dealer_hand = game["dealer"]

        while self.calculate_points(dealer_hand) < 17:
            dealer_hand.append(self.draw_card())

        dealer_score = self.calculate_points(dealer_hand)

        result = f"🧑‍💼 **Dealer:** {', '.join(dealer_hand)} ({dealer_score})\n" \
                 f"🧑 **Bạn:** {', '.join(game['player'])} ({player_score})\n"

        if dealer_score > 21 or player_score > dealer_score:
            result += f"🎉 **{user.mention} bạn thắng!**"
        elif dealer_score == player_score:
            result += f"🤝 **{user.mention} hòa với Dealer.**"
        else:
            result += f"💸 **{user.mention} bạn thua rồi.**"

        await channel.send(result)
        await self.end_game(user.id)

# Setup Cog
async def setup(bot):
    await bot.add_cog(Cash(bot))
    await bot.add_cog(AddMoney(bot))
    await bot.add_cog(Daily(bot))  # Thêm Daily vào đây
    await bot.add_cog(Coinflip(bot))
    await bot.add_cog(Bank(bot))
    await bot.add_cog(Give(bot))
    await bot.add_cog(Blackjack(bot))

# Sử dụng setup_hook để tải cog khi bot khởi động
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")
    await setup(bot)

bot.setup_hook = on_ready

# Chạy bot
bot.run("MTM5NDAyNjgxMjc5OTA2MjA3Ng.G4DSCu.J9NL-8-UF2WgUo4GrXRZfcWFEj_FSVz3wBCBOY")  # Thay YOUR_BOT_TOKEN bằng token thật của bạn!
