import discord
from discord.ext import commands
import sqlite3
import random
import time
import asyncio
import os  # Thêm để lấy token từ biến môi trường

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="h", intents=intents, help_command=None)

conn = sqlite3.connect('hazel_bank.db')
c = conn.cursor()

# Tạo bảng nếu chưa có
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 50000, last_daily INTEGER DEFAULT 0,
              last_w INTEGER DEFAULT 0, exp INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
              bank INTEGER DEFAULT 0, last_checkin INTEGER DEFAULT 0)''')
conn.commit()

def create_user(user_id):
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def get_balance(user_id):
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    return c.fetchone()[0]

def update_balance(user_id, amount):
    balance = get_balance(user_id) + amount
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
    conn.commit()

@bot.event
async def on_ready():
    print(f"Hazel_Bot đã sẵn sàng với ID: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user or not message.guild:
        return
    user_id = message.author.id
    create_user(user_id)
    exp_gain = random.randint(5, 20)
    c.execute("SELECT exp, level FROM users WHERE user_id = ?", (user_id,))
    exp, level = c.fetchone()
    exp += exp_gain
    if exp >= level * 100:
        level += 1
        exp = 0
        await message.channel.send(f"🎉 {message.author.display_name} đã lên cấp {level}!")
    c.execute("UPDATE users SET exp = ?, level = ? WHERE user_id = ?", (exp, level, user_id))
    conn.commit()
    await bot.process_commands(message)

@bot.command(name="commands")
async def show_commands(ctx):
    help_text = """
📜 **Danh sách lệnh Hazel_Bot:**

💰 Tiền tệ:
- `hcf <số tiền> <heads/tails>` – Cược tung đồng xu
- `hdaily` – Nhận 50.000 icoin mỗi ngày
- `hcheckin` – Điểm danh mỗi ngày để nhận icoin
- `hw` – Nhận icoin ngẫu nhiên mỗi 10 phút
- `hcash` – Xem số dư tiền mặt và ngân hàng
- `hgive <@user> <số tiền>` – Chuyển tiền cho người khác

🏦 Ngân hàng:
- `hdep <số tiền>` – Gửi tiền vào ngân hàng
- `hwith <số tiền>` – Rút tiền từ ngân hàng

🎲 Minigame:
- `hslot <số tiền>` – Máy quay slot
- `hnumber <1-10>` – Đoán số từ 1 đến 10

🏆 Xếp hạng:
- `htop cash` – Top người nhiều tiền nhất
- `htop level` – Top người có cấp cao nhất
"""
    await ctx.send(help_text)

@bot.command(name="cf")
@commands.cooldown(1, 10, commands.BucketType.user)
async def cf(ctx, amount: int, choice: str = None):
    user_id = ctx.author.id
    user_name = f"**{ctx.author.display_name or ctx.author.name}**"

    create_user(user_id)
    balance = get_balance(user_id)
    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0.")
    if amount > balance:
        return await ctx.send(f"❌ Bạn không đủ icoin để cược {amount:,}. Số dư hiện tại: {balance:,} icoin.")

    if choice is None:
        choice = "heads"
    else:
        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            return await ctx.send("❌ Lựa chọn phải là 'heads' hoặc 'tails' nếu bạn ghi thêm.")

    icon_map = {"heads": "🟡", "tails": "🟢"}
    spin_icons = ["🟡", "🟢"]

    message = await ctx.send(f"{user_name} đặt cược {amount:,} icoin và chọn {choice.capitalize()}")

    for _ in range(3):
        for icon in spin_icons:
            await asyncio.sleep(0.25)
            await message.edit(content=f"{user_name} đặt cược {amount:,} icoin và chọn {choice.capitalize()}\n\nKết quả là {icon}...")

    await asyncio.sleep(0.3)

    result = random.choice(["heads", "tails"])
    icon_result = icon_map[result]

    if choice == result:
        win_amount = amount * 2
        update_balance(user_id, win_amount)
        final_msg = f"{user_name} đặt cược {amount:,} icoin và chọn {choice.capitalize()}\n\nKết quả là {icon_result} và bạn **thắng {win_amount:,} icoin**!"
    else:
        update_balance(user_id, -amount)
        final_msg = f"{user_name} đặt cược {amount:,} icoin và chọn {choice.capitalize()}\n\nKết quả là {icon_result} và bạn mất hết tiền cược."

    await message.edit(content=final_msg)

@bot.command(name="cfall")
@commands.cooldown(1, 10, commands.BucketType.user)
async def cfall(ctx):
    user_id = ctx.author.id
    user_name = f"**{ctx.author.display_name}**"
    create_user(user_id)
    balance = get_balance(user_id)
    if balance <= 0:
        return await ctx.send(f"{user_name} bạn không có đủ icoin để cược.")

    amount = min(balance, 500000)
    user_choice = random.choice(["heads", "tails"])
    result = random.choice(["heads", "tails"])
    spin_icons = ["🟡", "🟢"]

    message = await ctx.send(f"{user_name} đặt cược {amount:,} icoin và chọn {user_choice.capitalize()}")

    for _ in range(3):
        for icon in spin_icons:
            await asyncio.sleep(0.25)
            await message.edit(content=f"{user_name} đặt cược {amount:,} icoin và chọn {user_choice.capitalize()}\n\nKết quả là {icon}...")

    await asyncio.sleep(0.3)
    icon_result = "🟡"

    if user_choice == result:
        win_amount = amount * 2
        update_balance(user_id, win_amount)
        final_msg = f"{user_name} đặt cược {amount:,} icoin và chọn {user_choice.capitalize()}\n\nKết quả là {icon_result} và bạn **thắng {win_amount:,} icoin**!"
    else:
        update_balance(user_id, -amount)
        final_msg = f"{user_name} đặt cược {amount:,} icoin và chọn {user_choice.capitalize()}\n\nKết quả là {icon_result} và bạn mất hết tiền cược."

    await message.edit(content=final_msg)

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    create_user(user_id)
    current = int(time.time())
    c.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    last = c.fetchone()[0]
    if current - last >= 86400:
        update_balance(user_id, 50000)
        c.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (current, user_id))
        conn.commit()
        await ctx.send("✅ Bạn đã nhận 50,000 icoin mỗi ngày.")
    else:
        await ctx.send("⏳ Bạn phải chờ 24h để nhận tiếp.")

@bot.command()
async def checkin(ctx):
    user_id = ctx.author.id
    create_user(user_id)
    current = int(time.time())
    c.execute("SELECT last_checkin FROM users WHERE user_id = ?", (user_id,))
    last = c.fetchone()[0]
    if current - last >= 86400:
        bonus = random.randint(1000, 15000)
        update_balance(user_id, bonus)
        c.execute("UPDATE users SET last_checkin = ? WHERE user_id = ?", (current, user_id))
        conn.commit()
        await ctx.send(f"✅ Bạn đã điểm danh và nhận được {bonus:,} icoin.")
    else:
        await ctx.send("⏳ Bạn đã điểm danh hôm nay rồi. Hãy quay lại sau 24h.")

@bot.command()
async def cash(ctx):
    user_id = ctx.author.id
    create_user(user_id)
    balance = get_balance(user_id)
    c.execute("SELECT bank FROM users WHERE user_id = ?", (user_id,))
    bank = c.fetchone()[0]
    await ctx.send(f"💰 {ctx.author.display_name} hiện có: {balance:,} icoin | 💼 Trong ngân hàng: {bank:,} icoin")

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    sender = ctx.author.id
    receiver = member.id
    create_user(sender)
    create_user(receiver)
    if amount <= 0:
        await ctx.send("Số tiền phải > 0.")
        return
    if get_balance(sender) < amount:
        await ctx.send("Bạn không đủ tiền.")
        return
    update_balance(sender, -amount)
    update_balance(receiver, amount)
    await ctx.send(f"💸 {ctx.author.display_name} đã chuyển {amount:,} icoin cho {member.display_name}.")

@bot.command(name="w")
async def hw(ctx):
    user_id = ctx.author.id
    create_user(user_id)
    current = int(time.time())
    c.execute("SELECT last_w FROM users WHERE user_id = ?", (user_id,))
    last = c.fetchone()[0]

    if current - last >= 600:
        reward = random.randint(1000, 300000)
        update_balance(user_id, reward)
        c.execute("UPDATE users SET last_w = ? WHERE user_id = ?", (current, user_id))
        conn.commit()
        user_name = f"**{ctx.author.display_name}**"
        actions = [
            "đã đi ăn cướp tiền bà già để kiếm được",
            "nhờ việc đi bán ma túy đã kiếm được",
            "đi dọc đường đã nhặt",
            "móc bóp bà hàng xóm kiếm được",
            "đã chịu 1 đấm của Sám Phùng để lấy",
            "ăn cức người khác và kiếm được"
        ]
        action = random.choice(actions)
        await ctx.send(f"{user_name} {action} {reward:,}Cash 🟡")
    else:
        await ctx.send("⏳ Bạn cần đợi 10 phút để dùng lại `hw`.")

@bot.command()
async def dep(ctx, amount: int):
    user_id = ctx.author.id
    create_user(user_id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("❌ Số tiền không hợp lệ hoặc không đủ.")
    update_balance(user_id, -amount)
    c.execute("UPDATE users SET bank = bank + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    await ctx.send(f"🏦 Gửi thành công {amount:,} icoin vào ngân hàng.")

@bot.command(name="with")
async def with_(ctx, amount: int):
    user_id = ctx.author.id
    create_user(user_id)
    c.execute("SELECT bank FROM users WHERE user_id = ?", (user_id,))
    bank = c.fetchone()[0]
    if amount <= 0 or bank < amount:
        return await ctx.send("❌ Số tiền không hợp lệ hoặc không đủ trong ngân hàng.")
    update_balance(user_id, amount)
    c.execute("UPDATE users SET bank = bank - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    await ctx.send(f"🏧 Rút thành công {amount:,} icoin từ ngân hàng.")

@bot.command()
async def slot(ctx, amount: int):
    user_id = ctx.author.id
    create_user(user_id)
    if amount <= 0 or get_balance(user_id) < amount:
        return await ctx.send("❌ Số tiền cược không hợp lệ hoặc không đủ.")
    symbols = ["🍒", "🍋", "🍉", "⭐", "💎"]
    result = [random.choice(symbols) for _ in range(3)]
    win = result.count(result[0]) == 3
    update_balance(user_id, amount if win else -amount)
    msg = f"| {' | '.join(result)} |\n"
    msg += "🎉 Bạn thắng!" if win else "😢 Bạn thua!"
    await ctx.send(msg)

@bot.command()
async def number(ctx, guess: int):
    user_id = ctx.author.id
    create_user(user_id)
    if guess < 1 or guess > 10:
        return await ctx.send("⚠️ Nhập số từ 1 đến 10.")
    answer = random.randint(1, 10)
    if guess == answer:
        prize = 50000
        update_balance(user_id, prize)
        await ctx.send(f"🎉 Đúng rồi! Số là {answer}. Bạn nhận {prize} icoin.")
    else:
        await ctx.send(f"❌ Sai rồi! Số đúng là {answer}.")

@bot.command()
async def top(ctx, mode="cash"):
    if mode not in ["cash", "level"]:
        return await ctx.send("⚠️ Dùng `htop cash` hoặc `htop level`.")
    if mode == "cash":
        c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    else:
        c.execute("SELECT user_id, level FROM users ORDER BY level DESC LIMIT 10")
    rows = c.fetchall()
    msg = "**🏆 TOP 10**\n"
    for i, (uid, value) in enumerate(rows, 1):
        user = await bot.fetch_user(uid)
        if mode == "cash":
            msg += f"{i}. {user.display_name} – {value:,} icoin\n"
        else:
            msg += f"{i}. {user.display_name} – Cấp {value}\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def addmoney(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Số tiền phải lớn hơn 0.")
    create_user(member.id)
    update_balance(member.id, amount)
    await ctx.send(f"💸 Đã thêm {amount:,} icoin cho {member.display_name}.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Vui lòng đợi {error.retry_after:.1f} giây trước khi dùng lại lệnh.")
    else:
        raise error

# ✅ Chạy bot bằng biến môi trường
bot.run(os.getenv("DISCORD_TOKEN"))