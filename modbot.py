# modbot.py
import os
import traceback
import sys
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get

CLI_CHANNEL = "bot-cli"
LOG_CHANNEL = "bot-log"

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='!')

# Check that the command was invoked by an admin
@bot.check
def is_admin(ctx):
    # Don't execute commands in private messages
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    if "Admin" not in [role.name for role in ctx.author.roles]:
        raise commands.MissingRole("Admin")
    return True

# Check that the command was invoked in the proper channel
@bot.check
def bot_cli(ctx):
    # Because the is_admin check runs before this, we can safely assume
    # that we are in a guild
    if ctx.message.channel.name != CLI_CHANNEL:
        raise commands.DisabledCommand()
    return True

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

# Log permission errors
@bot.event
async def on_command_error(ctx, error):
    # If a command was invoked in a private message
    if isinstance(error, commands.NoPrivateMessage):
        return
    # If a command was invoked by someone other than an admin
    elif isinstance(error, commands.MissingRole):
        error_name = "MissingRole"
    # If a command was invoked in the wrong channel
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.delete()
        error_name = "DisabledCommand"
    # Print the standard traceback for all other errors
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        return

    log_channel = get(ctx.guild.text_channels, name=LOG_CHANNEL)
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
    """Prints a hello world message"""
    await ctx.send("Hello World!")

@bot.command()
async def test(ctx):
    """Prints a test message"""
    await ctx.send("This is a test command.")

bot.run(token)
