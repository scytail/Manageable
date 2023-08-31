"""A module for cogs that manage system-wide processes."""
import datetime
import json
import traceback
from typing import Union

from discord.ext import commands
from discord import Message, Embed, Reaction, ClientUser

from src.cogs.base import ConfiguredCog


class GlobalErrorHandlingCog(ConfiguredCog):
    """A Cog class meant to passively watch for events on the server."""

    @commands.Cog.listener()
    async def on_command_error(self,
                               ctx: commands.Context,
                               exception: commands.errors):
        """Watches for uncaught errors and outputs the error to the console, as
        normal, while also emitting a more user-friendly message to the discord
        server.

        Inspired by
        https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612

        :param ctx:         The context of the server messages.
        :param exception:   The exception that was passed up the chain.
        """

        # Verify that a local handler hasn't already interfaced with the error
        if hasattr(ctx.command, 'on_error'):
            command = ctx.command
            self.logger.debug('Ignoring exception in command %s, as another '
                              'module has already handled it.', command)
            return

        # Handle missing roles or missing commands
        if isinstance(exception, (commands.MissingRole,
                                  commands.MissingAnyRole,
                                  commands.CommandNotFound)):
            exception_type = type(exception)
            error_message = 'Passing exception of type %s to public users.'
            self.logger.warning(error_message, exception_type)
            return await ctx.send(str(exception))
        #  Handle missing arguments to commands
        if isinstance(exception, commands.MissingRequiredArgument):
            exception_type = type(exception)
            error_message = 'Passing exception of type %s to public users.'
            self.logger.warning(error_message, exception_type)
            return await ctx.send('You are missing a required argument. '
                                  'Please consult the `help` command for more '
                                  'details.')

        # Output the default exception to the console
        # since it wasn't handled elsewhere
        command = ctx.command
        self.logger.error('Skipping exception in command %s: %s',
                          command,
                          exception)
        self.logger.debug(traceback.format_exc())
        return await ctx.send('An internal error occurred while processing '
                              'your command.')


class AirlockCog(ConfiguredCog):
    """A class supporting the airlock functionality (including the `accept`
    command)."""

    config_name = 'airlock'

    @commands.command()
    async def accept(self, ctx: commands.context):
        """The origin point for the accept command

        :param ctx: The command context.
        """

        # Check to make sure the command comes from a predefined channel.
        # If it doesn't, the command fails silently.
        airlock_channel = ConfiguredCog.config['content']['airlock_channel']
        if ctx.guild is None or ctx.channel.name != airlock_channel:
            self.logger.debug('Airlock release command was attempted to be '
                              'called from an invalid location.')
            await ctx.send(f'This command can only be accessed from the '
                           f'#{airlock_channel} channel.')
            return

        # Give the message sender a predefined role
        role_name = ConfiguredCog.config['content']['airlock_release_role']
        role = self.find_role_in_guild(role_name, ctx.guild)
        if not role:
            self.logger.error('Encountered an issue attempting to resolve the '
                              'airlock role specified in the config.')
            await ctx.send('There was an issue finding the role to give to '
                           'the sender.')
            return

        if self.member_contains_role(role.name, ctx.author):
            self.logger.warning('%s requested an airlock release when they '
                                'already had the role.', ctx.author.name)
            await ctx.send('You already have the airlock release role.')
            return

        self.logger.debug('Released %s from the airlock.', ctx.author.name)
        reason_message = 'User requested release from the airlock channel.'
        await ctx.author.add_roles(role, reason=reason_message)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """Watches for any messages sent in the airlock channel, and deletes
        them after five seconds.

           :param message:  The message that was sent in a place that the bot
                            can see.
           """
        airlock_channel = ConfiguredCog.config['content']['airlock_channel']
        airlock_channel_delete_delay = 5.0  # delay in seconds

        if (message.guild is not None and
                message.channel.name == airlock_channel):
            # delete any messages coming into the airlock channel
            self.logger.debug('Deleting a message in the airlock channel.')
            await message.delete(delay=airlock_channel_delete_delay)


class HelpCog(ConfiguredCog):
    """A class supporting the `help` functionality."""

    _left = '⏪'  # the left reaction for pagination
    _right = '⏩'  # the right reaction for pagination
    _mail = '📧'  # mail reaction for the requester's message

    @commands.command()
    async def help(self,
                   ctx: commands.context,
                   command: Union[str, None] = None):
        """The origin point for the `help` command. Supports help text
        pagination based on the config settings.

        :param ctx:     The command context.
        :param command: The command to query details for.
        """

        index: int = 0
        message = None
        action: callable = ctx.author.send
        request_start = datetime.datetime.now()

        # Build the embeds to send
        help_dict: dict = self._parse_help_text()
        if command is None:
            pages = self._build_help_summary(help_dict)
        else:
            pages = self._build_help_detail(help_dict, command)

        await ctx.message.add_reaction(self._mail)

        # Only allow pagination manipulation for 10 minutes
        pagination_timeout = datetime.timedelta(minutes=10)
        while datetime.datetime.now() - request_start < pagination_timeout:
            # Push the current embed to the user
            sent_message = await action(embed=pages[index])
            if sent_message is not None:
                message = sent_message

            # Add controls
            await message.add_reaction(self._left)
            await message.add_reaction(self._right)

            allow_decrease = index != 0
            allow_increase = index != len(pages) - 1

            # Check for reactions
            check_method = self._get_check_method(message,
                                                  allow_decrease,
                                                  allow_increase)
            react, _ = await self.bot.wait_for('reaction_add',
                                               check=check_method)
            if react.emoji == self._left:
                index -= 1
            elif react.emoji == self._right:
                index += 1
            action = message.edit

    @staticmethod
    def _parse_help_text() -> dict:
        """Parses the help text out into its corresponding data, converting
        color strings to their numeric integers.

        :return:    The parsed json data from the necessary data file, with
                    some processing done to a few color fields.
        """

        with open('data/helptext.json', encoding='utf-8') as help_text_file:
            help_text_dict = json.load(help_text_file)
            color = ConfiguredCog.convert_color(help_text_dict['color'])
            help_text_dict['color'] = color

        return help_text_dict

    def _build_help_summary(self, help_dict: dict) -> list:
        """Takes the help data and builds a list of embeds to output to the
        user as needed.

        :param help_dict:   The help text dictionary parsed from json.

        :return:    A list of `discord.Embed` objects that will be used as
                    pages when browsing the help command.
        """

        commands_per_embed = ConfiguredCog.config['help_commands_per_page']
        command_index = 0
        embed = None
        embed_list = []

        enabled_commands = self._get_enabled_commands(help_dict)

        # Build the paginated embeds for display,
        # using the dictionary we just compiled
        for command, command_data in enabled_commands.items():
            # Check if first command on the page; build a new embed if so
            if command_index % commands_per_embed == 0:
                prefix = ConfiguredCog.config['command_prefix']
                help_desc = help_dict['description'].format(prefix=prefix)
                embed = Embed(title=help_dict['title'],
                              description=help_desc,
                              color=help_dict['color'])

            # Add field
            command_desc = command_data['description']
            embed.add_field(name=command,
                            value=command_desc,
                            inline=False)

            # Save the embed as a page if we've finished the page
            if (command_index + 1) % commands_per_embed == 0:
                # Add the embed to the list and clear the current embed
                # (to prevent double-adding the embed)
                embed_list.append(embed)
                embed = None

            command_index += 1

        # Save the last embed as a page if it hasn't already been saved yet
        if embed is not None:
            embed_list.append(embed)

        # Build the footer, now that we have a fully compiled list of all the
        # ENABLED commands
        total_pages = len(embed_list)
        page_num = 1
        for embed in embed_list:
            embed.set_footer(text=f'Page {page_num}/{total_pages}')
            page_num += 1

        return embed_list

    def _build_help_detail(self, help_dict: dict, command_name: str) -> list:
        """Builds the embed data for the command detail.

        :param help_dict:       The data dictionary that has the help
                                information.
        :param command_name:    The command keyword to search the help
                                dictionary for.

        :return:    A list of `discord.Embed` objects, where each embed is a
                    page to display that contains help information.
        """

        embed_list: list = []

        enabled_commands = self._get_enabled_commands(help_dict)

        # Error catching for invalid commands
        full_command_name = None
        for command in enabled_commands:
            # note that the "key" is the `command` part of the help text, which
            # could have parameters described in it like so:
            # "warn <action> <user>", so we only need to validate against the
            # first word of the command for the user's query. If we succeed,
            # jot down the full key, so we can use that from now on.
            if command_name == command.split()[0]:
                full_command_name = command
                break

        if not full_command_name:
            # Command not found, return an error embed to the user
            embed = Embed(title=command_name,
                          description='Command not found',
                          color=help_dict['color'])
            embed.set_footer(text='Page 1/1')
            embed_list.append(embed)
            return embed_list

        # Build the basic description of the command
        command_data = enabled_commands[full_command_name]
        embed = Embed(title=full_command_name,
                      description=command_data['description'],
                      color=help_dict['color'])
        # Build out detail fields if needed
        for detail in command_data['details']:
            embed.add_field(name=detail['parameter'],
                            value=detail['description'],
                            inline=False)

        # details are not paginated yet, so just "pretend" for consistency
        embed.set_footer(text='Page 1/1')
        embed_list.append(embed)

        return embed_list

    def _get_enabled_commands(self, help_dict: dict) -> dict:
        """Compile a dictionary of all the valid commands from all the enabled
        cogs, where the key is the command, and the value is the description.

        :param help_dict:   The data dictionary that has the help information.

        :return:    A dictionary where the key is the command and the value is
                    a dict with a 'description' and 'details'
        """
        enabled_commands: dict = {}

        for cog_name in help_dict['cogs']:
            if self.is_cog_enabled(cog_name) or \
                    self.is_cog_enabled(cog_name) is None:
                cog_commands = help_dict['cogs'][cog_name]

                for cog_command_dict in cog_commands:
                    # Build command information
                    desc = cog_command_dict['description']
                    command_data = {'description': desc, 'details': []}
                    if 'details' in cog_command_dict:
                        command_data['details'] = cog_command_dict['details']

                    # Add the command and its details
                    # to the enabled commands dict
                    command_name = cog_command_dict['command']
                    enabled_commands[command_name] = command_data

        return enabled_commands

    def _get_check_method(self,
                          message: Message,
                          allow_decrease: bool,
                          allow_increase: bool) -> callable([..., bool]):
        """Builds and returns a method that can be plugged into a bot's check
        functionality. The method's allow_decrease and allow_increase variables
        will be "baked" into the method before it's passed to the bot, which
        will be able to alter the flow of functionality when watching for
        reacts.

        :param message:         The message instance that we are watching
                                reacts from.
        :param allow_decrease:  Whether to allow going one page back or not.
        :param allow_increase:  Whether to allow going one page forward or not.

        :return:    A method that takes some number of arguments and returns a
                    boolean on whether you can move to the page desired.
        """

        def _check(reaction: Reaction, user: ClientUser) -> bool:
            """Checks to see if the reaction can trigger the help pagination
            event.

            :param reaction:    The reaction to validate.
            :param user:        The user that sent the reaction.

            :return:    Whether the waited process should fire or not.
            """
            if reaction.message.id != message.id or user == self.bot.user:
                return False
            if allow_decrease and reaction.emoji == self._left:
                return True
            if allow_increase and reaction.emoji == self._right:
                return True
            return False

        return _check
