# blacklist_functions.py
import os

BLACKLIST_DIR = "blacklists/"

def load_blacklist(blacklists, name):
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

def delete_blacklist(blacklists, name):
    del blacklists[name]
    try:
        os.remove(BLACKLIST_DIR + name + ".txt")
    except:
        pass

def rename_blacklist(blacklists, before, after):
    blacklists[after] = blacklists[before]
    del blacklists[before]
    old_filename = BLACKLIST_DIR + before + ".txt"
    new_filename = BLACKLIST_DIR + after + ".txt"
    os.rename(old_filename, new_filename)
    