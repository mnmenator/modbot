# modbot.py
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='!')

@bot.check
def is_admin(ctx):
    # Don't execute commands outside of guilds
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    if "Admin" not in [role.name for role in ctx.author.roles]:
        raise commands.MissingRole("Admin")
    return True

@bot.check
def bot_cli(ctx):
    # Because the is_admin check runs before this, we can safely assume
    # that we are in a guild
    if ctx.message.channel.name != "bot-cli":
        raise commands.DisabledCommand()
    return True

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        return
    elif isinstance(error, commands.MissingRole):
        await ctx.message.delete()
        print("Someone other than an admin attempted this command!")
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.delete()
        print("Someone tried to execute this command outside of the cli channel!")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello World!")

bot.run(token)
