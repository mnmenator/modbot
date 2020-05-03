# strike_functions.py

SETTINGS_DIR = "settings/"
DEFAULT_SETTINGS = "strike_threshold 3 i\nstrike_expiration 60.0 f\npunishment kick s\n"

def load_settings(settings, name):
    settings[name] = {}
    try:
        # Try to create the file
        file = open(SETTINGS_DIR + name + ".txt", "x")
    except:
        # If creation fails, the file already exists
        pass
    else:
        # If creation succeeds, fill it with the default settings
        file.close()
        file = open(SETTINGS_DIR + name + ".txt", "w")
        file.write(DEFAULT_SETTINGS)
        file.close()
    with open(SETTINGS_DIR + name + ".txt", "r") as f:
        line = f.readline()
        while line:
            info = line.split()
            if info[2] == "i":
                settings[name][info[0]] = int(info[1])
            elif info[2] == "f":
                settings[name][info[0]] = float(info[1])
            else:
                settings[name][info[0]] = info[1]
            line = f.readline()

def delete_settings(settings, name):
    del settings[name]
    try:
        os.remove(SETTINGS_DIR + name + ".txt")
    except:
        pass

def rename_settings(settings, before, after):
    settings[after] = settings[before]
    del settings[before]
    old_filename = SETTINGS_DIR + before + ".txt"
    new_filename = SETTINGS_DIR + after + ".txt"
    os.rename(old_filename, new_filename)

def remove_strike(strikes, member):
    if member in strikes and strikes[member] > 0:
        strikes[member] -= 1

def init_strikes(strikes, guild):
    for member in guild.members:
        strikes[member] = 0

def clear_strikes(strikes, guild):
    for member in guild.members:
        del strikes[member]
