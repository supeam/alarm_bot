import discord
from discord.ext import commands, tasks
import datetime
import os
import json
from keep_alive import keep_alive

TOKEN = os.environ['TOKEN']  # ต้องตั้ง Environment Variable ชื่อ TOKEN ใน Replit
CHANNEL_ID = 1326096175748612200  # เปลี่ยนเป็น ID ของช่อง Discord ที่คุณใช้

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ รายชื่อสมาชิกเป็น User ID (int) : ชื่อเล่น
members = {
    327486022306758678: "โฟม",
    564079563840421888: "อิง",
    428101345401241601: "ฮาร์ท"
}

payment_status = {}

def reset_payment_status():
    month = datetime.datetime.now().strftime("%B")
    return {
        "โฟม": False,
        "อิง": False,
        "ฮาร์ท": False,
        "เดือน": month
    }

def save_status():
    with open("payment_status.json", "w", encoding="utf-8") as f:
        json.dump(payment_status, f, ensure_ascii=False)

def load_status():
    global payment_status
    try:
        with open("payment_status.json", "r", encoding="utf-8") as f:
            payment_status.update(json.load(f))
    except FileNotFoundError:
        payment_status.update(reset_payment_status())
        save_status()

@tasks.loop(time=datetime.time(hour=9, minute=0))
async def monthly_reminder():
    now = datetime.datetime.now()
    if now.day == 1:
        global payment_status
        payment_status = reset_payment_status()
        save_status()
        channel = bot.get_channel(CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            await channel.send("🔔 วันนี้วันที่ 1 แล้ว! อย่าลืมจ่ายเงินนะครับ 💸")

@bot.event
async def on_ready():
    load_status()
    monthly_reminder.start()
    print(f"[READY] Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID or message.author.bot:
        return

    if message.attachments:
        user_id = message.author.id
        if user_id in members:
            member_name = members[user_id]
            # เช็คสถานะ ถ้ายังไม่เคยจ่าย จะบันทึกและแจ้งเตือน
            if not payment_status.get(member_name, False):
                payment_status[member_name] = True
                save_status()
                await message.channel.send(f"{member_name} ได้จ่ายแล้ว ✅")
                await send_status(message.channel)
            else:
                # ถ้าจ่ายแล้ว แจ้งว่าจ่ายแล้ว ไม่ต้องส่งสถานะซ้ำ
                await message.channel.send(f"{member_name} คุณได้ทำการจ่ายแล้วครับ")
        else:
            await message.channel.send(f"ID {user_id} ยังไม่อยู่ในระบบ ❌")

    await bot.process_commands(message)

async def send_status(channel):
    status_lines = []
    for k, v in payment_status.items():
        if k == 'เดือน':
            continue
        if v:
            status_lines.append(f"{k} ได้จ่ายแล้ว ✅")
        else:
            status_lines.append(f"{k}: ยังไม่จ่าย ❌")
    await channel.send(f"📅 สถานะการจ่ายเงิน ({payment_status['เดือน']}):\n" + "\n".join(status_lines))

@bot.command()
async def เช็คสถานะ(ctx):
    await send_status(ctx.channel)

@bot.command()
async def รีเซ็ต(ctx):
    global payment_status
    payment_status = reset_payment_status()
    save_status()
    await ctx.send("🔁 รีเซ็ตสถานะจ่ายเงินเรียบร้อย")

keep_alive()
bot.run(TOKEN)
