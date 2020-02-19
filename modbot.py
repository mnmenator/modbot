# modbot.py
import os
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get

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
        error_name = "MissingRole"
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.delete()
        error_name = "DisabledCommand"

    log_channel = get(ctx.guild.text_channels, name="bot-log")
    if log_channel is None:
        return
    log = (
        f"{ctx.author.name} attempted to execute \"{ctx.message.content}\" "
        f"in the {ctx.channel.name} channel, "
        f"triggering the {error_name} exception."
    )
    await log_channel.send(log)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello World!")

@bot.command()
async def test(ctx):
    await ctx.send("Howdy Doody Gamers")

bot.run(token)
