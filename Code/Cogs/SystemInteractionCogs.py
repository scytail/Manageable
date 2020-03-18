import sys
import traceback
from discord.ext import commands
from Code.Cogs.ConfiguredCog import ConfiguredCog


class UserInteractionCog(ConfiguredCog):
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f'{member.display_name} joined.')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception: commands.errors):
        # Inspired by https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612

        # Verify that a local handler hasn't already interfaced with the error
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(exception, (commands.MissingRole, commands.MissingAnyRole)):
            return await ctx.send(str(exception))

        # Output the default exception to the console since it wasn't handled elsewhere
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        return await ctx.send('An internal error occurred while processing your command.')
