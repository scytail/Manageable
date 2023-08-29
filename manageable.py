"""Module for building and running a Manageable bot instance."""
import asyncio
from typing import TypeVar

from code.cogs import base
from code.cogs.mod_tools import UserWarnCog
from code.cogs.system_interactions import (GlobalErrorHandlingCog, AirlockCog,
                                           HelpCog)
from code.cogs.user_tools import RoleRequestCog, TagCog
from code.cogs.toys import CookieHuntCog, DiceRollerCog, AutoDrawingPromptCog

from discord.ext.commands.bot import Bot
from discord import Intents


def construct_bot() -> Bot:
    """Constructs a discord bot with the necessary intents

    :return:    An initialized, but empty, discord bot.
    """
    base.ConfiguredCog.logger.debug('Initializing bot.')

    intents = Intents.default()
    intents.members = True
    intents.message_content = True

    discord_bot = Bot(base.ConfiguredCog.config['command_prefix'],
                      help_command=None,
                      intents=intents)

    return discord_bot


T = TypeVar('T', bound='ConfiguredCog')


async def add_optional_cog(cog_type: T, discord_bot: Bot):
    """Adds a cog of the given type to the discord bot based on the config.

    :param cog_type:    The type of cog to create.
    :param discord_bot: The bot to add the cog to.
    """
    config_name = cog_type.config_name
    enable_cog = base.is_cog_enabled(config_name, base.ConfiguredCog.config)
    base.ConfiguredCog.logger.debug('%s Cog check resulted in: %s.',
                                    config_name,
                                    enable_cog)
    if enable_cog or enable_cog is None:
        base.ConfiguredCog.logger.debug('Adding %s Cog.', config_name)
        await discord_bot.add_cog(cog_type(discord_bot))
    else:
        base.ConfiguredCog.logger.debug('Skipping %s Cog.', config_name)


async def add_cog_functionality(discord_bot: Bot):
    """Adds cogs as needed to the provided bot.

    :param discord_bot: The bot to add Cogs to.
    """
    # Do not disable
    base.ConfiguredCog.logger.debug('Adding GlobalErrorHandling Cog.')
    await discord_bot.add_cog(GlobalErrorHandlingCog(discord_bot))

    # Do not disable
    base.ConfiguredCog.logger.debug('Adding Help Cog.')
    await discord_bot.add_cog(HelpCog(discord_bot))

    await add_optional_cog(TagCog, discord_bot)

    await add_optional_cog(UserWarnCog, discord_bot)

    await add_optional_cog(RoleRequestCog, discord_bot)

    await add_optional_cog(AirlockCog, discord_bot)

    await add_optional_cog(AutoDrawingPromptCog, discord_bot)

    await add_optional_cog(CookieHuntCog, discord_bot)

    await add_optional_cog(DiceRollerCog, discord_bot)


async def main():
    """Main entry point of the Manageable system. Should be called only when
    executing the software."""

    base.ConfiguredCog.logger.info('Constructing Manageable bot...')
    bot = construct_bot()

    async with bot:
        base.ConfiguredCog.logger.info('Attaching functionality...')
        await add_cog_functionality(bot)

        # Run the bot
        message = 'Launching Manageable with the specified bot token.'
        base.ConfiguredCog.logger.warning(message)
        await bot.start(base.ConfiguredCog.config['token'])


if __name__ == '__main__':
    asyncio.run(main())
