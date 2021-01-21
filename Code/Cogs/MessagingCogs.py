import datetime
import json
from discord.ext import commands
from discord import Embed, Message
from Code.Cogs.Base import ConfiguredCog
from math import ceil


class TagCog(ConfiguredCog):
    """A class supporting the `tag` command functionality.

    Methods
    -------
    tag     The origin point for the `tag` command.
    """

    @commands.command()
    async def tag(self, ctx: commands.Context, tag_name: str = None):
        """The origin point for the `tag` command.

        Parameters
        ----------
        ctx:        discord.ext.commands.Context    The command context.
        tag_name:   str                             The key string of the tag to query the config for.
        """

        if tag_name is not None:
            try:
                tag_data = ConfiguredCog.config['content']['tags'][tag_name]
            except KeyError:
                # No tag found, fail silently
                return

            # Build tag data
            color = ConfiguredCog.convert_color(self._get_tag_data_safe(tag_data, 'color'))
            if color is None:
                color = Embed.Empty

            title = self._get_tag_data_safe(tag_data, 'title')
            if title is None:
                # Tag title isn't set, but is required, set it to the tag name
                title = tag_name

            url = self._get_tag_data_safe(tag_data, 'url')
            description = self._get_tag_data_safe(tag_data, 'description')

            # Send embed
            message = Embed(color=color, title=title, url=url, description=description)
        else:
            # Send list of tags
            message = Embed(title='Available Tags',
                            description='Please do `tag <tag_name>` to display the tag contents.')
            for tag_name in ConfiguredCog.config['content']['tags'].keys():
                title = self._get_tag_data_safe(ConfiguredCog.config['content']['tags'][tag_name], 'title')
                if title is None:
                    # Tag title isn't set, but is required, set it to the tag name
                    title = tag_name

                message.add_field(name=tag_name, value=title)

        await ctx.send(embed=message)

    @staticmethod
    def _get_tag_data_safe(tag_data: dict, tag_name: str):
        """A static method to look up the tag name from a dictionary of tag data and fail safely if it can't be found.

        Parameters
        ----------
        tag_data:   dict    A dictionary of tags an their data, where the keys are strings referencing the tag's
                            name, and the values are dictionaries denoting the data to build the tag.
        tag_name:   str     The key to query in the provided data.

        Returns
        -------
        dict    If the tag name is found in the data's keys, return the corresponding dictionary value.
        None    If the tag's name was not found in the data's keys, return `None`.
        """

        try:
            return tag_data[tag_name]
        except KeyError:
            return None


class HelpCog(ConfiguredCog):
    """A class supporting the `help` functionality.

    Methods
    -------
    help    The origin point for the `help` command.
    """

    _left = '⏪'  # emote to use as the left reaction for pagination
    _right = '⏩'  # emote to use as the right reaction for pagination
    _mail = '📧'  # emote to use as the mail reaction for the requester's message

    @commands.command()
    async def help(self, ctx: commands.context, command: str = None):
        """The origin point for the `help` command. Supports help text pagination based on the config settings

        Parameters
        ----------
        ctx:        discord.ext.commands.context    The command context.
        command:    str|None                        The command to query details for
        """

        index: int = 0
        message = None
        action: callable = ctx.author.send
        request_start_time = datetime.datetime.now()

        # Build the embeds to send
        help_dict: dict = self._parse_help_text()
        if command is None:
            pages = self._build_help_summary(help_dict)
        else:
            pages = self._build_help_detail(help_dict, command)

        await ctx.message.add_reaction(self._mail)

        # Only allow pagination manipulation for 10 minutes
        while datetime.datetime.now()-request_start_time < datetime.timedelta(minutes=10):
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
            react, user = await self.bot.wait_for('reaction_add',
                                                  check=self._get_check_method(message, allow_decrease, allow_increase))
            if react.emoji == self._left:
                index -= 1
            elif react.emoji == self._right:
                index += 1
            action = message.edit

    @staticmethod
    def _parse_help_text() -> dict:
        """Parses the help text out into its corresponding data, converting color strings to their numeric integers.

        Returns
        -------
        dict    The parsed json data from the necessary data file,
                with some processing done to a few color fields.
        """

        with open('Data/helptext.json') as help_text_file:
            help_text_dict = json.load(help_text_file)
            help_text_dict['color'] = ConfiguredCog.convert_color(help_text_dict['color'])

        return help_text_dict

    def _build_help_summary(self, help_dict: dict) -> list:
        """Takes the help data and builds a list of embeds to output to the user as needed

        Parameters
        ----------
        help_dict:  dict    The help text dictionary parsed from json.

        Returns
        -------
        list    A list of `discord.Embed` objects that will be used as pages when browsing the help command
        """

        commands_per_embed: int = ConfiguredCog.config['help_commands_per_page']
        command_index: int = 0
        embed = None
        embed_list: list = []

        for command_key in help_dict['command_list']:
            command_summary = help_dict['command_list'][command_key]

            if self.is_cog_enabled(command_key) or \
               self.is_cog_enabled(command_key) is None:
                # Check if first command on the page
                if command_index % commands_per_embed == 0:
                    embed = Embed(title=help_dict['title'],
                                  description=help_dict['description'].format(
                                      prefix=ConfiguredCog.config['command_prefix']),
                                  color=help_dict['color'])

                # Add fields
                embed.add_field(name=command_summary['command'], value=command_summary['description'], inline=False)

                # Save the embed as a page if we've finished the page
                if (command_index + 1) % commands_per_embed == 0:
                    # Add the embed to the list and clear the current embed (to prevent double-adding the embed)
                    embed_list.append(embed)
                    embed = None

                command_index += 1

        # Save the last embed as a page if it hasn't already been saved yet
        if embed is not None:
            # Add the embed to the list and clear the current embed (to prevent double-adding the embed)
            embed_list.append(embed)

        # Build the footer, now that we have a fully compiled list of all the ENABLED commands
        total_pages = len(embed_list)
        page_num = 1
        for embed in embed_list:
            embed.set_footer(text=f'Page {page_num}/{total_pages}')
            page_num += 1

        return embed_list

    def _build_help_detail(self, help_dict: dict, command_id: str) -> list:
        """Builds the embed data for the command detail.

        Parameters
        ----------
        help_dict:  dict    The data dictionary that has the help information.
        command_id: str     The command keyword to search the help dictionary for.

        Returns
        -------
        list    A list of `discord.Embed` objects,
                where each embed is a page to display that contains help information.
        """

        embed_list: list = []
        if command_id not in help_dict['command_list'] or \
           not (self.is_cog_enabled(command_id) or
                self.is_cog_enabled(command_id) is None):
            # Command not found, return an error embed to the user
            embed = Embed(title=command_id, description='Command not found', color=help_dict['color'])
            embed_list.append(embed)
            return embed_list

        # Build the basic description of the  command
        command_data = help_dict['command_list'][command_id]
        embed = Embed(title=command_data['command'], description=command_data['description'], color=help_dict['color'])
        # Build out detail fields if needed
        if 'details' in command_data:
            for detail in command_data['details']:
                embed.add_field(name=detail['parameter'], value=detail['description'], inline=False)

        # TODO: Paginate the details
        embed.set_footer(text='Page 1/1')
        embed_list.append(embed)

        return embed_list

    def _get_check_method(self, message: Message, allow_decrease: bool, allow_increase: bool) -> callable([..., bool]):
        """Builds and returns a method that can be plugged into a bot's check functionality.
           The method's allow_decrease and allow_increase variables will be "baked" into the method before its passed to
           the bot, which will be able to alter the flow of functionality when watching for reacts.

        Parameters
        ----------
        message:        discord.Message     The message instance that we are watching reacts from.
        allow_decrease: bool                Whether to allow going one page back or not.
        allow_increase: bool                Whether to allow going one page forward or not.

        Returns
        -------
        callable([..., bool])   A method that takes some number of arguments and returns a boolean on whether you can
                                move to the page desired.
        """

        def check(reaction, user) -> bool:
            if reaction.message.id != message.id or user == self.bot.user:
                return False
            if allow_decrease and reaction.emoji == self._left:
                return True
            if allow_increase and reaction.emoji == self._right:
                return True
            return False

        return check
