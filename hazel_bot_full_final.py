import discord
from discord.ext import commands
import sqlite3
import random
import time
import asyncio
import os  # Thêm để lấy token từ biến môi trường

intents = discord.Intents.default()
intents.message_content = True
from keep_alive import keep_alive
keep_alive()

bot = commands.Bot(command_prefix="h", intents=intents, help_command=None)

conn = sqlite3.connect('hazel_bank.db')
c = conn.cursor()

# Tạo bảng nếu chưa có
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 50000,
    last_daily INTEGER DEFAULT 0,
    last_w INTEGER DEFAULT 0,
    exp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    bank INTEGER DEFAULT 0,
    last_checkin INTEGER DEFAULT 0,
    last_robbed_by INTEGER DEFAULT 0,
    last_robbed_time INTEGER DEFAULT 0
)
''')
conn.commit()

# Thêm cột nếu thiếu (cho DB cũ)
try:
    c.execute("ALTER TABLE users ADD COLUMN last_robbed_by INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE users ADD COLUMN last_robbed_time INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass


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

💰 __**Tiền tệ:**__
- `hcf <số tiền> <heads/tails>` – Cược tung đồng xu
- `hdaily` – Nhận 50.000 icoin mỗi ngày
- `hcheckin` – Điểm danh mỗi ngày để nhận icoin
- `hw` – Nhận icoin ngẫu nhiên mỗi 10 phút
- `hcash` – Xem số dư tiền mặt và ngân hàng
- `hgive <@user> <số tiền>` – Chuyển tiền cho người khác

🏦 __**Ngân hàng:**__
- `hdep <số tiền>` – Gửi tiền vào ngân hàng
- `hwith <số tiền>` – Rút tiền từ ngân hàng

🎲 __**Minigame:**__
- `hslot <số tiền>` – Máy quay slot
- `hnumber <1-10>` – Đoán số từ 1 đến 10
- `hbc <số tiền>` – Bài cào ba lá
- `htx <tài/xỉu> <số tiền>` – Chơi tài xỉu
- `hloto <số 00-99> <số tiền>` – Xổ số lô tô

🕵️‍♂️ __**Cướp & Báo công an:**__
- `hrob @người chơi` – Cướp icoin của người khác (10 phút cooldown)
- `hreport` – Báo công an nếu bạn bị cướp gần đây (15 phút cooldown)

🏆 __**Xếp hạng:**__
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
        return await ctx.send(f"❌ Bạn không đủ :cowoncy: để cược {amount:,}. Hiện có: {balance:,} :cowoncy:")

    if choice is None:
        choice = "heads"
    else:
        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            return await ctx.send("❌ Lựa chọn phải là 'heads' hoặc 'tails'.")

    icon_map = {"heads": "🟡", "tails": "🟢"}
    gif_url = "https://media.tenor.com/lcJeyA9vviIAAAAC/coin-flip.gif"

    embed = discord.Embed(title="🪙 Tung đồng xu!", color=discord.Color.gold())
    embed.add_field(name="Người chơi", value=user_name, inline=True)
    embed.add_field(name="Cược", value=f"{amount:,} :cowoncy:", inline=True)
    embed.add_field(name="Chọn", value=choice.capitalize(), inline=True)
    embed.set_image(url=gif_url)

    message = await ctx.send(embed=embed)

    await asyncio.sleep(3)

    result = random.choice(["heads", "tails"])
    icon_result = icon_map[result]

    if choice == result:
        update_balance(user_id, amount)
        outcome = f"🎉 {user_name} đã **thắng** {amount:,} :cowoncy:!"
        color = discord.Color.green()
    else:
        update_balance(user_id, -amount)
        outcome = f"💸 {user_name} đã **thua** và mất {amount:,} :cowoncy:."
        color = discord.Color.red()

    result_embed = discord.Embed(title="🎯 Kết quả tung đồng xu", color=color)
    result_embed.add_field(name="Kết quả", value=f"{icon_result} {result.upper()}", inline=True)
    result_embed.add_field(name="Bạn chọn", value=choice.upper(), inline=True)
    result_embed.add_field(name="Kết luận", value=outcome, inline=False)

    await message.edit(embed=result_embed)


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
    icon_result = {"heads": "🟡", "tails": "🟢"}[result]

    if user_choice == result:
        update_balance(user_id, amount)
        final_msg = f"{user_name} đặt cược {amount:,} icoin và chọn {user_choice.capitalize()}\n\nKết quả là {icon_result} và bạn **thắng {amount:,} icoin**!"
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
        amount = random.randint(50000, 500000)
        update_balance(user_id, amount)
        c.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (current, user_id))
        conn.commit()
        await ctx.send(f"🎁 Bạn đã nhận **{amount:,} icoin** từ phần thưởng mỗi ngày!")
    else:
        await ctx.send("⏳ Bạn đã nhận rồi, hãy quay lại sau 24h để nhận tiếp.")


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

    cooldown = 600  # 10 phút
    remaining = cooldown - (current - last)

    if remaining <= 0:
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
        minutes = remaining // 60
        seconds = remaining % 60
        await ctx.send(f"⏳ Bạn cần chờ **{minutes} phút {seconds} giây** nữa để dùng lại `hw`.")


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


@bot.command(name="rob")
@commands.cooldown(1, 600, commands.BucketType.user)  # 10 phút cooldown
async def hrob(ctx, member: discord.Member):
    robber_id = ctx.author.id
    victim_id = member.id

    if robber_id == victim_id:
        return await ctx.send("❌ Bạn không thể cướp chính mình.")

    create_user(robber_id)
    create_user(victim_id)

    c.execute("SELECT balance FROM users WHERE user_id = ?", (victim_id,))
    victim_balance = c.fetchone()[0]

    if victim_balance < 10000:
        return await ctx.send(f"❌ {member.display_name} không có đủ icoin để bị cướp (cần ít nhất 10,000).")

    amount = random.randint(10000, min(1000000, victim_balance))
    update_balance(victim_id, -amount)
    update_balance(robber_id, amount)

    c.execute("UPDATE users SET last_robbed_by = ?, last_robbed_time = ? WHERE user_id = ?", (robber_id, int(time.time()), victim_id))
    conn.commit()

    await ctx.send(f"🦹‍♂️ {ctx.author.display_name} đã cướp {amount:,} icoin từ {member.display_name} thành công!")

@bot.command(name="report")
@commands.cooldown(1, 900, commands.BucketType.user)  # 15 phút cooldown
async def hreport(ctx):
    user_id = ctx.author.id
    create_user(user_id)

    c.execute("SELECT last_robbed_by, last_robbed_time FROM users WHERE user_id = ?", (user_id,))
    data = c.fetchone()
    if not data or data[0] == 0:
        return await ctx.send("🚓 Bạn chưa bị ai cướp gần đây để báo công an.")

    robber_id, robbed_time = data
    now = int(time.time())

    if now - robbed_time > 600:
        return await ctx.send("⌛ Đã quá 10 phút kể từ khi bị cướp. Công an không giúp được nữa.")

    if random.randint(1, 100) <= 40:
        refund = random.randint(10000, 300000)
        update_balance(user_id, refund)
        update_balance(robber_id, -refund)
        c.execute("UPDATE users SET last_robbed_by = 0, last_robbed_time = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        robber_user = await bot.fetch_user(robber_id)
        await ctx.send(f"✅ Công an đã bắt được {robber_user.display_name} và trả lại bạn {refund:,} icoin!")
    else:
        await ctx.send("❌ Công an không tìm được thủ phạm. Bạn không lấy lại được tiền.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if ctx.command.name == "rob":
            minutes = int(error.retry_after) // 60
            seconds = int(error.retry_after) % 60
            return await ctx.send(f"⏳ Bạn phải chờ {minutes} phút {seconds} giây nữa để dùng lại `hrob`.")
        elif ctx.command.name == "report":
            minutes = int(error.retry_after) // 60
            seconds = int(error.retry_after) % 60
            return await ctx.send(f"⏳ Bạn phải chờ {minutes} phút {seconds} giây nữa để dùng lại `hreport`.")
        else:
            await ctx.send(f"⏳ Vui lòng đợi {error.retry_after:.1f} giây trước khi dùng lại lệnh.")
    else:
        raise error

@bot.command()
@commands.has_permissions(administrator=True)
async def addmoney(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Số tiền phải lớn hơn 0.")
    create_user(member.id)
    update_balance(member.id, amount)
    await ctx.send(f"💸 Đã thêm {amount:,} icoin cho {member.display_name}.")



@bot.command(name="baicao")
@commands.cooldown(1, 15, commands.BucketType.user)  # 15 giây chờ
async def hbaicao(ctx, amount: int):
    user_id = ctx.author.id
    create_user(user_id)

    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0.")

    balance = get_balance(user_id)
    if balance < amount:
        return await ctx.send("❌ Bạn không đủ icoin để cược.")

    # Trừ tiền cược tạm thời
    update_balance(user_id, -amount)

    # Chia 3 lá bài (giá trị từ 1 đến 13, tương ứng A → K)
    cards = [random.randint(1, 13) for _ in range(3)]
    total = sum(min(card, 10) for card in cards) % 10

    # Tính kết quả
    result_msg = f"🃏 Bài của bạn: {cards[0]}, {cards[1]}, {cards[2]} (Tổng nút: {total})\n"
    
    if total >= 7:
        winnings = int(amount * 1.5)
        update_balance(user_id, winnings + amount)  # Trả lại tiền cược + thưởng
        result_msg += f"🎉 Bạn thắng! Nhận được {winnings:,} icoin!"
    elif total == 0:
        result_msg += f"💀 Bù trừ sạch bách! Bạn mất {amount:,} icoin!"
    else:
        result_msg += f"😢 Thua rồi! Bạn mất {amount:,} icoin."

    await ctx.send(result_msg)


@bot.command(name="taixiu")
@commands.cooldown(1, 15, commands.BucketType.user)  # 15 giây chờ
async def htaixiu(ctx, choice: str, amount: int):
    user_id = ctx.author.id
    create_user(user_id)

    choice = choice.lower()
    if choice not in ["tài", "xỉu"]:
        return await ctx.send("❌ Lựa chọn không hợp lệ! Vui lòng chọn `tài` hoặc `xỉu`.")

    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0.")

    balance = get_balance(user_id)
    if balance < amount:
        return await ctx.send("❌ Bạn không đủ icoin để cược.")

    # Trừ tiền cược tạm thời
    update_balance(user_id, -amount)

    # Gieo xúc xắc
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "xỉu" if 4 <= total <= 10 else "tài"

    result_msg = (
        f"🎲 Kết quả: {dice[0]} + {dice[1]} + {dice[2]} = **{total}** → **{result.upper()}**\n"
        f"🧠 Bạn chọn: **{choice.upper()}**\n"
    )

    if choice == result:
        update_balance(user_id, amount * 2)
        result_msg += f"🎉 Bạn đã thắng và nhận được {amount:,} icoin!"
    else:
        result_msg += f"💸 Bạn đã thua và mất {amount:,} icoin!"

    await ctx.send(result_msg)


@bot.command(name="loto")
@commands.cooldown(1, 15, commands.BucketType.user)  # 15 giây cooldown mỗi người dùng
async def hloto(ctx, number: int, amount: int):
    user_id = ctx.author.id
    create_user(user_id)

    if number < 0 or number > 99:
        return await ctx.send("❌ Vui lòng chọn số từ 0 đến 99.")

    if amount <= 0:
        return await ctx.send("❌ Số tiền cược phải lớn hơn 0.")

    balance = get_balance(user_id)
    if balance < amount:
        return await ctx.send("❌ Bạn không đủ icoin để cược.")

    # Trừ tiền cược
    update_balance(user_id, -amount)

    # Quay số
    lucky = random.randint(0, 99)

    result_msg = f"🎰 Kết quả xổ số: **{lucky:02d}**\n🎯 Bạn chọn: **{number:02d}**\n"

    if number == lucky:
        winnings = amount * 70
        update_balance(user_id, winnings)
        result_msg += f"🎉 Chúc mừng! Bạn đã trúng số và nhận được {winnings:,} icoin!"
    else:
        result_msg += f"💸 Rất tiếc, bạn không trúng. Mất {amount:,} icoin."

    await ctx.send(result_msg)



# ✅ Chạy bot bằng biến môi trường
bot.run(os.getenv("DISCORD_TOKEN"))
