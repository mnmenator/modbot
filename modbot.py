# modbot.py
import os
import traceback
import sys
from dotenv import load_dotenv
from discord import HTTPException
from discord.ext import commands
from discord.utils import get

CLI_CHANNEL = "bot-cli"
LOG_CHANNEL = "bot-log"
BLACKLIST_DIR = "blacklists/"

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='!')

blacklists = {}

def load_blacklist(name):
    blacklists[name] = []
    try:
        # Try to create the file
        file = open(BLACKLIST_DIR + name + ".txt", "x")
    except:
        # If creation fails, the file already exists
        pass
    else:
        # If creation succeeds, close it so it can be opened for reading
        file.close()
    with open(BLACKLIST_DIR + name + ".txt", "r") as f:
        words = f.readlines()
        # Add contents to its blacklist
        blacklists[name] = [word.strip() for word in words]

def delete_blacklist(name):
    del blacklists[name]
    try:
        os.remove(BLACKLIST_DIR + name + ".txt")
    except:
        pass

def rename_blacklist(before, after):
    blacklists[after] = blacklists[before]
    del blacklists[before]
    old_filename = BLACKLIST_DIR + before + ".txt"
    new_filename = BLACKLIST_DIR + after + ".txt"
    os.rename(old_filename, new_filename)

async def message_screen(message):
    for word in blacklists[message.guild.name]:
        if word in message.content:
            await message.channel.send("Bad word detected")
            return
    await message.channel.send("All clear")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    # Load blacklists once the bot connects
    names = [guild.name for guild in bot.guilds]
    for name in names:
        load_blacklist(name)

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot
    if message.author.id == bot.user.id:
        return
    # Process commands normally
    if(message.content[0] == '!'):
        await bot.process_commands(message)
    else:
        # Only evaluate messages sent in guilds
        if message.guild is None:
            return
        await message_screen(message)

@bot.event
async def on_guild_join(guild):
    # Create a new blacklist and file when the bot joins a server
    load_blacklist(guild.name)

@bot.event
async def on_guild_remove(guild):
    # Remove the blacklist and file when the bot leaves a server
    # Also if a server is deleted
    delete_blacklist(guild.name)

@bot.event
async def on_guild_update(before, after):
    # If a server is renamed, update the blacklist and file
    if before.name != after.name:
        rename_blacklist(before.name, after.name)

# Log permission errors
@bot.event
async def on_command_error(ctx, error):
    # If the command is not recognized.
    # This error is raised before any checks are triggered, which
    # is why we need to do some otherwise redundant checks here
    if isinstance(error, commands.CommandNotFound):
        if ctx.guild is None:
            return
        elif "Admin" not in [role.name for role in ctx.author.roles]:
            await message_screen(ctx.message)
        elif ctx.channel.name != CLI_CHANNEL:
            await ctx.message.delete()
        else:
            await ctx.send(
                f"That command is not recognized. Type \"!help\" "
                f"for a list of commands."
            )
        return
    # If a command was invoked in a private message
    elif isinstance(error, commands.NoPrivateMessage):
        return
    # If a command was invoked by someone other than an admin
    elif isinstance(error, commands.MissingRole):
        error_name = "MissingRole"
    # If a command was invoked without the proper permissions
    elif isinstance(error, commands.MissingPermissions):
        error_name = "MissingPermissions"
    # If a command was invoked in the wrong channel
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.delete()
        error_name = "DisabledCommand"

    # Print the standard traceback for all other errors
    else:
        traceback.print_exception(type(error), error,
                                  error.__traceback__, file=sys.stderr)
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

@bot.command()
async def hello(ctx):
    """Prints a hello world message"""
    await ctx.send("Hello World!")

@bot.command()
async def test(ctx):
    """Prints a test message"""
    await ctx.send("This is a test command.")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, *names):
    """Kicks a user from the server"""
    if len(names) == 0:
        await ctx.send_help(ctx.command)
    for name in names:
        member = get(ctx.guild.members, name=name)
        if member is None:
            await ctx.send("There is no member named \"" + name + "\"")
        else:
            try:
                await member.kick()
            except HTTPException:
                await ctx.send("Failed to kick \"" + name + "\"")
            else:
                await ctx.send("Successfully kicked \"" + name + "\"")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, *names):
    """Bans a user from the server"""
    if len(names) == 0:
        await ctx.send_help(ctx.command)
    for name in names:
        member = get(ctx.guild.members, name=name)
        if member is None:
            await ctx.send("There is no member named \"" + name + "\"")
        else:
            try:
                await member.ban()
            except HTTPException:
                await ctx.send("Failed to ban \"" + name + "\"")
            else:
                await ctx.send("Successfully banned \"" + name + "\"")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_user(ctx, *names):
    """Unbans a user from the server"""
    if len(names) == 0:
        await ctx.send_help(ctx.command)
    bans = await ctx.guild.bans()
    banned_users = [ban.user for ban in bans]
    for name in names:
        member = get(banned_users, name=name)
        if member is None:
            await ctx.send("There is no banned member named \"" + name + "\"")
        else:
            try:
                await ctx.guild.unban(member)
            except HTTPException:
                await ctx.send("Failed to unban \"" + name + "\"")
            else:
                await ctx.send("Successfully unbanned \"" + name + "\"")


@bot.group()
async def blacklist(ctx):
    """Interacts with the blacklist"""
    if ctx.invoked_subcommand is None:
        # Print the help text if no subcommand is called
        await ctx.send_help(ctx.command)

@blacklist.command()
async def show(ctx):
    """Prints all blacklisted words"""
    await ctx.send(blacklists[ctx.guild.name])

@blacklist.command()
async def add(ctx, *words):
    """Adds words to the blacklist"""
    for word in words:
        if word in blacklists[ctx.guild.name]:
            await ctx.send("\"" + word + "\" is already blacklisted.")
        else:
            blacklists[ctx.guild.name].append(word)
            # Add new word to the blacklist file
            with open(BLACKLIST_DIR + ctx.guild.name + ".txt", "a") as f:
                f.write(word + "\n")
    # Print updated blacklist
    await ctx.send(blacklists[ctx.guild.name])

@blacklist.command()
async def remove(ctx, *words):
    """Removes words from the blacklist"""
    for word in words:
        if word not in blacklists[ctx.guild.name]:
            await ctx.send("\"" + word + "\" is not blacklisted.")
        else:
            blacklists[ctx.guild.name].remove(word)
            # Remove word from the blacklist file
            with open(BLACKLIST_DIR + ctx.guild.name + ".txt", "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if line != (word + "\n"):
                        f.write(line)
                f.truncate()
    # Print updated blacklist
    await ctx.send(blacklists[ctx.guild.name])

bot.run(token)
