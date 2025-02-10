import os
import discord
import requests
import random
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Load environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
NEWS_CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))

# Set up bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Store image generation limits
image_limits = {}

# Auto Slowmode
@bot.event
async def on_message(message):
    if message.channel.id == NEWS_CHANNEL_ID:
        await message.channel.edit(slowmode_delay=10)
    await bot.process_commands(message)

# Welcome DM with Avatar Image
@bot.event
async def on_member_join(member):
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    username = member.name

    response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(response.content)).resize((100, 100))
    
    base = Image.new("RGB", (400, 200), (30, 30, 30))
    draw = ImageDraw.Draw(base)
    font = ImageFont.load_default()
    
    draw.text((120, 80), f"Welcome {username}!", fill="white", font=font)
    base.paste(avatar, (10, 50))
    
    img_buffer = BytesIO()
    base.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    await member.send("Welcome to the server!", file=discord.File(img_buffer, filename="welcome.png"))

# Fun Games
@bot.command()
async def roll(ctx):
    await ctx.send(f"🎲 You rolled: {random.randint(1, 6)}")

@bot.command()
async def flip(ctx):
    await ctx.send(f"🪙 {random.choice(['Heads', 'Tails'])}")

# Pokémon Info Command
@bot.command()
async def pokemon(ctx, name: str):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        await ctx.send(f"**{data['name'].capitalize()}**\nHeight: {data['height']}\nWeight: {data['weight']}")
    else:
        await ctx.send("Pokémon not found!")

# Anime Quotes
@bot.command()
async def animequote(ctx):
    response = requests.get("https://animechan.xyz/api/random")
    if response.status_code == 200:
        data = response.json()
        await ctx.send(f"**{data['quote']}**\n- {data['character']} ({data['anime']})")
    else:
        await ctx.send("Couldn't fetch a quote.")

# Anime Search & Character Info
@bot.command()
async def anime(ctx, *, query: str):
    response = requests.get(f"https://api.jikan.moe/v4/anime?q={query}")
    if response.status_code == 200:
        data = response.json()["data"][0]
        await ctx.send(f"**{data['title']}**\n{data['url']}")
    else:
        await ctx.send("Anime not found!")

@bot.command()
async def character(ctx, *, name: str):
    response = requests.get(f"https://api.jikan.moe/v4/characters?q={name}")
    if response.status_code == 200:
        data = response.json()["data"][0]
        await ctx.send(f"**{data['name']}**\n{data['url']}")
    else:
        await ctx.send("Character not found!")

# Meme Generator
@bot.command()
async def meme(ctx):
    response = requests.get("https://meme-api.com/gimme")
    if response.status_code == 200:
        data = response.json()
        await ctx.send(data["url"])
    else:
        await ctx.send("Couldn't fetch a meme.")

# AI Image Generation (Limited to 20 per day)
@bot.command()
async def imagine(ctx, *, prompt: str):
    user_id = ctx.author.id
    today = datetime.now().date()

    if user_id in image_limits and image_limits[user_id]['date'] == today:
        if image_limits[user_id]['count'] >= 20:
            await ctx.send("⚠️ You’ve reached your daily limit of 20 images!")
            return
        image_limits[user_id]['count'] += 1
    else:
        image_limits[user_id] = {'date': today, 'count': 1}

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
        json={"prompt": prompt, "n": 1, "size": "1024x1024"}
    )
    if response.status_code == 200:
        data = response.json()
        await ctx.send(data["data"][0]["url"])
    else:
        await ctx.send("Failed to generate image.")

# Anime News (Crunchyroll & ANN)
@tasks.loop(hours=1)
async def anime_news():
    channel = bot.get_channel(NEWS_CHANNEL_ID)
    if channel:
        crunchyroll_url = "https://www.crunchyroll.com/news/rss"
        ann_url = "https://www.animenewsnetwork.com/news/rss.xml"

        await channel.send(f"📰 **Latest Anime News:**\nCrunchyroll: <{crunchyroll_url}>\nAnime News Network: <{ann_url}>")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    anime_news.start()

bot.run(TOKEN)
