import json
import logging
from discord.ext import commands

# The config file to load data from.
CONFIG_FILE = 'Config/config.json'


def build_logger(enable_debug: bool) -> logging.Logger:
    """Builds a logger instance that is used for various system logging.

    Parameters
    ----------
    enable_debug:   bool    A boolean toggle of whether to enable debug messages to get logged or not.

    Returns
    -------
    logging.Logger  The configured logger instance that can be logged to.
    """

    # Set lowest logging level
    if enable_debug:
        logger_base_level = logging.DEBUG
    else:
        logger_base_level = logging.INFO

    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

    # Create logger management class
    logger = logging.getLogger('main logger')
    logger.setLevel(logger_base_level)

    # Create file logger
    file_logger = logging.FileHandler('Data/debug.log')
    file_logger.setLevel(logger_base_level)
    file_logger.setFormatter(formatter)

    # Create console logger
    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.WARNING)  # console output should only be important information
    console_logger.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_logger)
    logger.addHandler(console_logger)

    return logger


def load_config(filename: str) -> dict:
    """Loads the specified json config file into memory for usage.

    Parameters
    ----------
    filename:   str     A valid path and filename from which the json configuration will be loaded.

    Returns
    -------
    dict    A dictionary parsed directly from the JSON file

    Exceptions
    ----------
    ValueError  if the filename is empty or not a vaild string, this method will throw a value error
    """

    if filename is None or filename == '' or type(filename) is not str:
        raise ValueError('filename must be a valid, non-empty string.')

    with open(filename) as config_file:
        json_dict = json.load(config_file)

    return dict(json_dict)


class ConfiguredCog(commands.Cog):
    """A Base class containing some general data and methods for all the implemented Cogs to use.

    Class Variables
    ---------------
    config: dict    Builds the configuration dictionary on import so that it's easily accessible.

    Instance Variables
    ------------------
    bot:    discord.ext.commands.Bot    A discord bot instance for self-referential purposes.

    Methods
    -------
    __init__        Sets up the Cog for general usage.
    convert_color   A static class method for use processing stringified hex codes into integers.
    """

    config: dict = load_config(CONFIG_FILE)
    logger: logging.Logger = build_logger(config['verbose_logging'])

    def __init__(self, bot: commands.Bot):
        """Initializes the Base class for usage

        Parameters
        ----------
        bot:    discord.ext.commands.Bot    A discord bot instance which will be saved within the class instance.
        """

        self.bot: commands.Bot = bot

    @staticmethod
    def convert_color(color_hex_code: str):
        """A static method used for processing stringified hex codes into integers

        Parameters
        ----------
        color_hex_code: str     A hex code to parse. Can also be `None`.

        Returns
        -------
        int     If the hex code is a string that is 4 or 7 characters long (with the first character being a #),
                it will return that as an integer.
        Object  If the hex code does not meet the conditionals above, it will return the argument as passed in
        """

        if color_hex_code is None or (len(color_hex_code) != 4 and len(color_hex_code) != 7):
            return color_hex_code

        color_hex_code = color_hex_code[1:]  # Crop out the hash tag at the start
        return int(color_hex_code, 16)
