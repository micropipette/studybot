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
