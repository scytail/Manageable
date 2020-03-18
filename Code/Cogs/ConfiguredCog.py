from discord.ext import commands
import json


def _load_config(filename: str) -> dict:
    if filename is None or filename == '' or type(filename) is not str:
        raise ValueError('filename must be a valid, non-empty string.')

    with open(filename) as config_file:
        json_dict = json.load(config_file)

    return json_dict


class ConfiguredCog(commands.Cog):
    config = _load_config('Config/config.json')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def convert_color(color_hex_code: str):
        if color_hex_code is None or (len(color_hex_code) != 4 and len(color_hex_code) != 7):
            return color_hex_code

        color_hex_code = color_hex_code[1:]  # Crop out the hash tag at the start
        return int(color_hex_code, 16)
