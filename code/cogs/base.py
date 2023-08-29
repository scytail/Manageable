"""A Module for base Cog functionality."""
import json
import logging
from typing import Optional, Union

from discord import Role, Guild, Member
from discord.ext import commands

# The config file to load data from.
CONFIG_FILE = 'config/config.json'


def build_logger(enable_debug: bool) -> logging.Logger:
    """Builds a logger instance that is used for various system logging.

    :param enable_debug:    A boolean toggle of whether to enable debug
                            messages to get logged or not.

    :return:    The configured logger instance that can be logged to.
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
    file_logger = logging.FileHandler('data/debug.log')
    file_logger.setLevel(logger_base_level)
    file_logger.setFormatter(formatter)

    # Create console logger
    console_logger = logging.StreamHandler()
    # console output should only be important information
    console_logger.setLevel(logging.WARNING)
    console_logger.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_logger)
    logger.addHandler(console_logger)

    return logger


def load_config(filename: str) -> dict:
    """Loads the specified json config file into memory for usage.

    :param filename:    A valid path and filename from which the json
                        configuration will be loaded.

    :return:    A dictionary parsed directly from the JSON file.

    :except ValueError: if the filename is empty or not a valid string.
    """

    if filename is None or filename == '' or not isinstance(filename, str):
        raise ValueError('filename must be a valid, non-empty string.')

    with open(filename, encoding='utf-8') as config_file:
        json_dict = json.load(config_file)

    return dict(json_dict)


def is_cog_enabled(cog_name: str, config_dict: dict) -> Optional[bool]:
    """Checks to see if the given cog name is enabled in the provided dictionary

    :param cog_name:    The name of the cog to validate in the config.
    :param config_dict: The config dictionary to check enabled settings

    :return:    Returns true if true in the dictionary, or false for anything
                else. If it cannot find the data in the
    provided config, returns None.
    """

    if 'features' not in config_dict['content'] or \
       cog_name not in config_dict['content']['features']:
        # didn't find the cog in the config,
        # return nothing to convey this issue.
        return None

    # There's a chance the user accidentally sets the data to something other
    # than a boolean. If we find a "true" value, we should return true,
    # otherwise we should return false. This ensures method return type
    # integrity.
    enabled_setting = config_dict['content']['features'][cog_name]
    if isinstance(enabled_setting, bool) and enabled_setting:
        return True

    return False


class ConfiguredCog(commands.Cog):
    """A Base class containing some general data and methods for all the
    implemented Cogs to use.

    :var config:    The configuration dictionary, built on import, so that it's
                    easily accessible.
    :var logger:    The logger, built on import, used for logging events that
                    occur within a cog.
    :var bot:       A discord bot instance for self-referential purposes.
    """

    config: dict = load_config(CONFIG_FILE)
    logger: logging.Logger = build_logger(config['verbose_logging'])
    config_name: str

    def __init__(self, bot: commands.Bot):
        """Initializes the Base class for usage

        :param bot: A discord bot instance which will be saved within the class
                    instance.
        """

        self.bot: commands.Bot = bot

    @staticmethod
    def convert_color(color_code: Union[str, None]) -> Union[int, str, None]:
        """A static method used for processing serialized hex codes into
        integers.

        :param color_code: A hex code to parse or `None`.

        :return:    If the hex code is a string that is 4 or 7 characters long
                    (with the first character being a #), it will return that
                    as an integer. If the hex code does not meet the
                    conditionals above, it will return the argument as passed
                    in.
        """

        if (color_code is None or
                (len(color_code) != 4 and len(color_code) != 7)):
            return color_code

        # Crop out the hashtag at the start
        color_code = color_code[1:]
        return int(color_code, 16)

    def is_cog_enabled(self, cog_name: str) -> Optional[bool]:
        """Exposes base methodology of is_cog_enabled in the class structure,
        using the class's embedded config.

        :param cog_name:    The cog to check if enabled

        :return:    Returns true if true in the dictionary, or false for
                    anything else. If it cannot find the data in the provided
                    config, returns None.
        """
        return is_cog_enabled(cog_name, self.config)

    @staticmethod
    def find_role_in_guild(role_name_query: str,
                           guild: Guild) -> Optional[Role]:
        """Finds a role with the provided name in a guild.

        Please note that this will find the first (lowest) role with the
        provided name. Be careful if the guild has multiple roles with the same
        role name. Also keep in mind that the role search *is* case-sensitive.

        :param role_name_query: The name of the role to search the guild for.
        :param guild:           The guild to validate the role name against.

        :return:    Returns the role in the class, or None if no role exists in
                    the guild.
        """
        for role in guild.roles:
            if role.name == role_name_query:
                # found the role with the provided name
                return role

        # didn't find the role
        return None

    @staticmethod
    def member_contains_role(role_name_query: str, member: Member) -> bool:
        """Validates that the provided member has a role with the given name.

        :param role_name_query: The name of the role to search the guild for.
        :param member:          The guild to validate the role name against.

        :return:    True if the member contains the role, or False otherwise.
        """
        for role in member.roles:
            if role.name == role_name_query:
                # found the role with the provided name
                return True

        # didn't find the role
        return False
