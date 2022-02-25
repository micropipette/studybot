def locale(ctx):
    '''
    Gets guild ID or author id -- for use in DB accessing
    '''
    return ctx.guild_id if ctx.guild_id else ctx.author.id


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
