import discord
from discord.ext import commands, tasks
import datetime
import os
import json
from keep_alive import keep_alive

TOKEN = os.environ['TOKEN']
CHANNEL_ID = 1326096175748612200  # ใส่ Channel ID ที่คุณต้องการให้บอททำงาน

intents = discord.Intents.default()
intents.message_content = True  # สำคัญ ต้องเปิด!
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# รายชื่อสมาชิกที่สามารถจ่ายเงินได้
members = {
    "lawganeyyeol.": "โฟม",
    "supeam": "อิง",
    "heart2952": "ฮาร์ท"
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

@tasks.loop(time=datetime.time(hour=9, minute=0))  # ทุกวันเวลา 9:00 AM
async def monthly_reminder():
    now = datetime.datetime.now()
    if now.day == 1:
        global payment_status
        payment_status = reset_payment_status()  # รีเซ็ตสถานะใหม่ทุกเดือน
        save_status()
        channel = bot.get_channel(CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            await channel.send("🔔 วันนี้วันที่ 1 แล้ว! อย่าลืมจ่ายเงินนะครับ 💸")

@bot.event
async def on_ready():
    load_status()
    monthly_reminder.start()

@bot.event
async def on_message(message):
    print(f"[DEBUG] ได้รับข้อความจาก: {message.author} ในช่อง {message.channel.name}")
    print(f"[DEBUG] แนบไฟล์: {message.attachments}")

    if message.channel.id != CHANNEL_ID or message.author.bot:
        return

    if message.attachments:
        username = message.author.name
        print(f"[DEBUG] ผู้ส่งแนบไฟล์: {username}")
        if username in members:
            member_name = members[username]
            payment_status[member_name] = True
            save_status()
            await message.channel.send(f"{member_name} ได้จ่ายแล้ว ✅")
            await send_status(message.channel)
        else:
            await message.channel.send(f"ชื่อ {username} ยังไม่อยู่ในระบบ ❌")

    await bot.process_commands(message)

async def send_status(channel):
    status_lines = [f"{k}: {'จ่ายแล้ว ✅' if v else 'ยังไม่จ่าย ❌'}" for k, v in payment_status.items() if k != 'เดือน']
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

keep_alive()  # เรียกก่อน bot.run(TOKEN)
bot.run(TOKEN)
