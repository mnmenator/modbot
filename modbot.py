# modbot.py
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command()
@commands.has_role("Admin")
async def hello(ctx):
    await ctx.send("Hello World!")

@hello.error
async def hello_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        print("Someone other than an admin attempted this command!")
    elif isinstance(error, commands.NoPrivateMessage):
        print("Someone tried to execute this command in a private message!")

bot.run(token)
