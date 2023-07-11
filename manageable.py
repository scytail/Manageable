import discord.ext.commands
from discord.ext.commands.bot import Bot
from discord import Intents
import Code.Cogs.Base as Base
from Code.Cogs.ModToolsCogs import UserWarnCog, AutoDrawingPrompt
from Code.Cogs.MessagingCogs import HelpCog, TagCog, CookieHuntCog, DiceRollerCog
from Code.Cogs.SystemInteractionCogs import GlobalErrorHandlingCog, RoleRequestCog, AirlockCog
import asyncio


async def build_discord_bot() -> Bot:
    # Build the bot
    Base.ConfiguredCog.logger.info('Constructing Manageable bot...')
    Base.ConfiguredCog.logger.debug(f'Building bot.')

    intents = Intents.default()
    intents.members = True  # Among others, the help command needs the members intent to monitor reactions
    intents.message_content = True  # We need this intent so that the bot actually registers when a command is called

    discord_bot = Bot(Base.ConfiguredCog.config['command_prefix'], help_command=None, intents=intents)

    # Add the necessary cogs
    Base.ConfiguredCog.logger.info('Attaching functionality...')

    # Do not disable
    Base.ConfiguredCog.logger.debug('Adding GlobalErrorHandling Cog.')
    await discord_bot.add_cog(GlobalErrorHandlingCog(discord_bot))

    # Do not disable
    Base.ConfiguredCog.logger.debug('Adding Help Cog.')
    await discord_bot.add_cog(HelpCog(discord_bot))

    enable_cog = Base.is_cog_enabled('tag', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'Tag Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding Tag Cog.')
        await discord_bot.add_cog(TagCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping Tag Cog.')

    enable_cog = Base.is_cog_enabled('warn', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'UserWarn Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding UserWarn Cog.')
        await discord_bot.add_cog(UserWarnCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping UserWarn Cog.')

    enable_cog = Base.is_cog_enabled('role', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'RoleRequest Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding RoleRequest Cog.')
        await discord_bot.add_cog(RoleRequestCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping RoleRequest Cog.')

    enable_cog = Base.is_cog_enabled('airlock', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'Airlock Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding Airlock Cog.')
        await discord_bot.add_cog(AirlockCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping Airlock Cog.')

    enable_cog = Base.is_cog_enabled('autoDrawingPrompt', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'AutoDrawingPrompt Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding AutoDrawingPrompt Cog.')
        await discord_bot.add_cog(AutoDrawingPrompt(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping AutoDrawingPrompt Cog.')

    enable_cog = Base.is_cog_enabled('cookieHunt', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'CookieHunt Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding CookieHunt Cog.')
        await discord_bot.add_cog(CookieHuntCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping CookieHunt Cog.')

    enable_cog = Base.is_cog_enabled('diceRoller', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'diceRoller Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding DiceRoller Cog.')
        await discord_bot.add_cog(DiceRollerCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping DiceRoller Cog.')

    return discord_bot


if __name__ == '__main__':
    # Build the bot
    bot = asyncio.run(build_discord_bot())

    # Run the bot
    Base.ConfiguredCog.logger.warning('Launching Manageable with the specified bot token.')
    bot.run(Base.ConfiguredCog.config['token'])
