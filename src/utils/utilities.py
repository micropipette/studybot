from config import cfg
import time

bot_prefix = cfg["Settings"]["prefix"].strip("\"")
startup_time = None


def set_start_time(time):
    '''
    Sets the startup time for the bot,
    so that we can use it to calculate the uptime of the bot
    '''
    global startup_time
    startup_time = time


def get_uptime() -> float:
    '''
    Returns uptime in seconds.
    '''
    return time.perf_counter() - startup_time

def textToEmoji(s) -> str:
    '''
    Converts text to equivalent emoji
    '''
    lookupTable = {
                "a": "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
                "b": "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                "c": "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
                "d": "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
                "e": "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
                "f": "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
                "g": "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
                "h": "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
                "i": "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
                "j": "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
                "k": "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
                "l": "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
                "m": "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
                "n": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
                "o": "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
                "p": "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
                "q": "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
                "r": "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
                "s": "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
                "t": "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
                "u": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                "v": "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
                "w": "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
                "x": "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
                "y": "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
                "z": "\N{REGIONAL INDICATOR SYMBOL LETTER Z}"}
    return lookupTable[s]


def emojiToText(s) -> str:
    '''
    Converts emoji to closest real text representation (lowercase output)
    Note: Will strip spaces.
    '''
    lookupTable = {
        u"\U0001F1E6": "a",
        u"\U0001F1E7": "b",
        u"\U0001F1E8": "c",
        u"\U0001F1E9": "d",
        u"\U0001F1EA": "e",
        u"\U0001F1EB": "f",
        u"\U0001F1EC": "g",
        u"\U0001F1ED": "h",
        u"\U0001F1EE": "i",
        u"\U0001F1EF": "j",
        u"\U0001F1F0": "k",
        u"\U0001F1F1": "l",
        u"\U0001F1F2": "m",
        u"\U0001F1F3": "n",
        u"\U0001F1F4": "o",
        u"\U0001F1F5": "p",
        u"\U0001F1F6": "q",
        u"\U0001F1F7": "r",
        u"\U0001F1F8": "s",
        u"\U0001F1F9": "t",
        u"\U0001F1FA": "u",
        u"\U0001F1FB": "v",
        u"\U0001F1FC": "w",
        u"\U0001F1FD": "x",
        u"\U0001F1FE": "y",
        u"\U0001F1FF": "z",
        "0️⃣": 0,
        "1️⃣": 1,
        "2️⃣": 2,
        "3️⃣": 3,
        "4️⃣": 4,
        "5️⃣": 5,
        "6️⃣": 6,
        "7️⃣": 7,
        "8️⃣": 8,
        "9️⃣": 9}

    newS = ''

    i = 0

    while i < len(s):
        if s[i] in lookupTable:
            newS += lookupTable[s[i]]
            i += 1
        else:
            newS += s[i]
        i += 1
    return newS


def locale(ctx):
    '''
    Gets guild ID or author id -- for use in DB accessing
    '''
    return ctx.guild.id if ctx.guild else ctx.author.id
