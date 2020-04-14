# modbot.py
import traceback
import sys
import blacklist_functions as b
import strike_functions as s
from threading import Timer
from dotenv import load_dotenv
from os import getenv
from discord import HTTPException
from discord.ext import commands
from discord.utils import get

CLI_CHANNEL = "bot-cli"
LOG_CHANNEL = "bot-log"
COMMAND_PREFIX = '!'

load_dotenv()
token = getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

blacklists = {}
strikes = {}
settings = {}

async def punish(member):
    if settings[member.guild.name]["punishment"] == "kick":
        await member.kick()
    elif settings[member.guild.name]["punishment"] == "ban":
        await member.ban()

async def message_screen(message):
    for word in blacklists[message.guild.name]:
        if word in message.content.lower():
            strikes[message.author] += 1
            if strikes[message.author] >= settings[message.guild.name]["strike_threshold"]:
                warning = (
                    f"Your message in {message.guild.name} has been deleted "
                    f"for containing \"{word}\". You have been removed from "
                    f"the server for accumulating "
                    f"{settings[message.guild.name]['strike_threshold']} strikes"
                )
            else:
                t = Timer(settings[message.guild.name]["strike_expiration"],
                          s.remove_strike, args=(strikes, message.author))
                t.start()
                warning = (
                    f"Your message in {message.guild.name} has been deleted "
                    f"for containing \"{word}\". You have "
                    f"{strikes[message.author]} strikes, which will expire "
                    f"after a given time. If you get {settings[message.guild.name]['strike_threshold']} "
                    f"strikes, you will be removed from the server"
                )
            await log_strike(message, word)
            await message.author.send(warning)
            if strikes[message.author] >= settings[message.guild.name]["strike_threshold"]:
                await punish(message.author)
            await message.delete()
            return

async def log_strike(message, bad_word):
    log_channel = get(message.guild.text_channels, name=LOG_CHANNEL)
    if log_channel is None:
        return
    if strikes[message.author] >= settings[message.guild.name]["strike_threshold"]:
        log = (
            f"{message.author.name} said \"{message.content}\" in the "
            f"{message.channel.name} channel, which was flagged for "
            f"containing \"{bad_word}\". They have been removed from the "
            f"server for reaching {settings[message.guild.name]['strike_threshold']} strikes"
        )
    else:
        log = (
            f"{message.author.name} said \"{message.content}\" in the "
            f"{message.channel.name} channel, which was flagged for "
            f"containing \"{bad_word}\". They now have "
            f"{strikes[message.author]} strikes"
        )
    await log_channel.send(log)

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    # Load blacklists once the bot connects
    names = [guild.name for guild in bot.guilds]
    for name in names:
        b.load_blacklist(blacklists, name)
        s.load_settings(settings, name)
    # Initialize strikes
    for guild in bot.guilds:
        for member in guild.members:
            strikes[member] = 0

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot
    if message.author.id == bot.user.id:
        return
    # Process commands normally
    if(message.content[0] == COMMAND_PREFIX):
        await bot.process_commands(message)
    else:
        # Only evaluate messages sent in guilds
        if message.guild is not None:
            await message_screen(message)

@bot.event
async def on_guild_join(guild):
    # Create a new blacklist and file when the bot joins a server
    b.load_blacklist(blacklists, guild.name)
    s.load_settings(settings, guild.name)
    s.init_strikes(strikes, guild)

@bot.event
async def on_guild_remove(guild):
    # Remove the blacklist and file when the bot leaves a server
    # or the server is deleted
    b.delete_blacklist(blacklists, guild.name)
    s.delete_settings(settings, guild.name)
    s.clear_strikes(strikes, guild)

@bot.event
async def on_guild_update(before, after):
    # If a server is renamed, update the blacklist and file
    if before.name != after.name:
        b.rename_blacklist(blacklists, before.name, after.name)
        s.rename_settings(settings, before.name, after.name)

@bot.event
async def on_member_join(member):
    # Initialize strikes when a member joins a server
    strikes[member] = 0;

@bot.event
async def on_member_remove(member):
    # Clear strikes when a member leaves a server
    del strikes[member]

# Log permission errors
@bot.event
async def on_command_error(ctx, error):
    #If the command has a local error handler, call that instead
    if hasattr(ctx.command, 'on_error'):
        return
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
                f"for a list of commands"
            )
        return
    # If a command was invoked in a private message
    elif isinstance(error, commands.NoPrivateMessage):
        return
    # If a command is missing a required argument
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
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
        f"triggering the {error_name} exception"
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

@bot.command()
async def strike_count(ctx, *names):
    """Prints a user's strike count"""
    if len(names) == 0:
        await ctx.send_help(ctx.command)
    for name in names:
        member = get(ctx.guild.members, name=name)
        if member is None:
            await ctx.send("There is no member named \"" + name + "\"")
        else:
            await ctx.send(name + " has " + (str)(strikes[member]) + " strikes")

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
            await ctx.send("\"" + word + "\" is already blacklisted")
        else:
            blacklists[ctx.guild.name].append(word)
            # Add new word to the blacklist file
            with open(b.BLACKLIST_DIR + ctx.guild.name + ".txt", "a") as f:
                f.write(word + "\n")
    # Print updated blacklist
    await ctx.send(blacklists[ctx.guild.name])

@blacklist.command()
async def remove(ctx, *words):
    """Removes words from the blacklist"""
    for word in words:
        if word not in blacklists[ctx.guild.name]:
            await ctx.send("\"" + word + "\" is not blacklisted")
        else:
            blacklists[ctx.guild.name].remove(word)
            # Remove word from the blacklist file
            with open(b.BLACKLIST_DIR + ctx.guild.name + ".txt", "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if line != (word + "\n"):
                        f.write(line)
                f.truncate()
    # Print updated blacklist
    await ctx.send(blacklists[ctx.guild.name])

@bot.group()
async def configure(ctx):
    """Configures blacklist punishment criteria"""
    if ctx.invoked_subcommand is None:
        # Print the help text if no subcommand is called
        await ctx.send_help(ctx.command)

@configure.command()
async def show(ctx):
    """Prints configurable parameters and their current values"""
    await ctx.send(
        f"strike_threshold = {settings[ctx.guild.name]['strike_threshold']}\n"
        f"strike_expiration = {settings[ctx.guild.name]['strike_expiration']} seconds\n"
        f"punishment = {settings[ctx.guild.name]['punishment']}"
    )

@configure.command()
async def strike_threshold(ctx, threshold: int):
    """Changes the number of strikes needed before a punishment"""
    if threshold < 1:
        await ctx.send("Please specify a number of strikes greater than 0")
        return
    settings[ctx.guild.name]["strike_threshold"] = threshold
    new_settings = (
        f"strike_threshold {threshold} i\n"
        f"strike_expiration {settings[ctx.guild.name]['strike_expiration']} f\n"
        f"punishment {settings[ctx.guild.name]['punishment']} s\n"
    )
    with open(s.SETTINGS_DIR + ctx.guild.name + ".txt", "w") as f:
        f.write(new_settings)

    await ctx.send("Users will now be punished after accumulating " +
                    str(threshold) + " strikes")

@strike_threshold.error
async def strike_threshold_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Please specify an integer")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
    else:
        traceback.print_exception(type(error), error,
                                  error.__traceback__, file=sys.stderr)

@configure.command()
async def strike_expiration(ctx, expiration: float):
    """Changes how many seconds strikes take to expire"""
    if expiration <= 0:
        await ctx.send("Please specify a number greater than 0")
        return
    settings[ctx.guild.name]["strike_expiration"] = expiration
    new_settings = (
        f"strike_threshold {settings[ctx.guild.name]['strike_threshold']} i\n"
        f"strike_expiration {expiration} f\n"
        f"punishment {settings[ctx.guild.name]['punishment']} s\n"
    )
    with open(s.SETTINGS_DIR + ctx.guild.name + ".txt", "w") as f:
        f.write(new_settings)
    await ctx.send("Strikes will now expire after " + str(expiration) +
                   " seconds")

@strike_expiration.error
async def strike_expiration_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Please specify a numeric input")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
    else:
        traceback.print_exception(type(error), error,
                                  error.__traceback__, file=sys.stderr)

@configure.command()
async def punishment(ctx, punishment):
    """Changes if users are kicked or banned after reaching the strike threshold"""
    if punishment not in ["ban", "kick"]:
        await ctx.send("Please specify \"ban\" or \"kick\"")
    else:
        settings[ctx.guild.name]["punishment"] = punishment
        new_settings = (
        f"strike_threshold {settings[ctx.guild.name]['strike_threshold']} i\n"
        f"strike_expiration {settings[ctx.guild.name]['strike_expiration']} f\n"
        f"punishment {punishment} s\n"
    )
    with open(s.SETTINGS_DIR + ctx.guild.name + ".txt", "w") as f:
        f.write(new_settings)
        await ctx.send("Changed punishment to " + punishment)

bot.run(token)
