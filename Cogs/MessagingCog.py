import datetime
import json
from discord.ext import commands
from discord import Embed
from Cogs.ConfiguredCog import ConfiguredCog, convert_color
from math import ceil

left = '⏪'
right = '⏩'


class SendMessageCog(ConfiguredCog):
    @commands.command()
    async def codex(self, ctx: commands.context):
        color = ConfiguredCog.config['content']['codex_links']['color']
        wa_link = ConfiguredCog.config['content']['codex_links']['world_anvil']
        doc_link = ConfiguredCog.config['content']['codex_links']['google_doc']

        message = Embed(title='World Anvil Link', color=color, url=wa_link)
        await ctx.send(embed=message)

        message = Embed(title='Google Docs Link', color=color, url=doc_link)
        await ctx.send(embed=message)

    @commands.command()
    async def help(self, ctx: commands.context, command: str = None):
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

        await ctx.message.add_reaction('📧')

        # Only allow pagination manipulation for 10 minutes
        while datetime.datetime.now()-request_start_time < datetime.timedelta(minutes=10):
            # Push the current embed to the user
            sent_message = await action(embed=pages[index])
            if sent_message is not None:
                message = sent_message

            # Add controls
            await message.add_reaction(left)
            await message.add_reaction(right)

            allow_decrease = index != 0
            allow_increase = index != len(pages) - 1

            # Check for reactions
            react, user = await self.bot.wait_for('reaction_add',
                                                  check=self._get_check_method(message, allow_decrease, allow_increase))
            if react.emoji == left:
                index -= 1
            elif react.emoji == right:
                index += 1
            action = message.edit

    @staticmethod
    def _parse_help_text() -> dict:
        with open('Data/helptext.json') as help_text_file:
            help_text_dict = json.load(help_text_file)
            help_text_dict['color'] = convert_color(help_text_dict['color'])

        return help_text_dict

    @classmethod
    def _build_help_summary(cls, help_dict: dict) -> list:
        commands_per_embed: int = ConfiguredCog.config['help_commands_per_page']
        command_index: int = 0
        embed = None
        embed_list: list = []
        page_num: int = 1

        for command_key in help_dict['command_list']:
            command_summary = help_dict['command_list'][command_key]

            # Check if first command on the page
            if command_index % ConfiguredCog.config['help_commands_per_page'] == 0:
                embed = Embed(title=help_dict['title'],
                              description=help_dict['description'],
                              color=help_dict['color'])

            # Add fields
            embed.add_field(name=command_summary['command'], value=command_summary['description'], inline=False)

            # Save the embed as a page if we've finished the page
            if command_index % commands_per_embed == commands_per_embed - 1 or \
               command_index == len(help_dict['command_list'])-1:
                # Build the footer
                total_pages = ceil(len(help_dict['command_list']) / ConfiguredCog.config['help_commands_per_page'])
                embed.set_footer(text=f'Page {page_num}/{total_pages}')
                # Add the embed to the list
                embed_list.append(embed)
                # Increment the page counter
                page_num += 1

            command_index += 1

        return embed_list

    @classmethod
    def _build_help_detail(cls, help_dict: dict, command_id: str) -> list:
        embed_list: list = []
        if not command_id in help_dict['command_list']:
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

    def _get_check_method(self, message, allow_decrease, allow_increase) -> callable([..., bool]):
        # This method returns a method that can be plugged into a bot's check functionality.
        # The method's allow_decrease and allow_increase variables will be "baked" into the method before its passed
        # to the bot, which will be able to alter the flow of functionality when watching for reacts.
        def check(reaction, user) -> bool:
            if reaction.message.id != message.id or user == self.bot.user:
                return False
            if allow_decrease and reaction.emoji == left:
                return True
            if allow_increase and reaction.emoji == right:
                return True
            return False

        return check
