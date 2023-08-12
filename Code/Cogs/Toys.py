from datetime import datetime, timedelta
import json
import urllib.request
from enum import Enum
from random import randint, sample, choices
from typing import Optional
from discord.ext import commands, tasks
from discord import Embed, TextChannel
from Code.Cogs.Base import ConfiguredCog
from Code.Data import DataAccess
from Code.Base.Parsing import DiceLexer, DiceParser


class CookieHuntSugarOptions(Enum):
    """An enum listing out all the available sugar command options."""
    HIGH = 'high'


class CookieHuntTarget(Enum):
    """An enum listing out all the available target options."""
    CLAIMER = 'claimer'
    LEADER = 'leader'


class CookieHuntCog(ConfiguredCog):
    """A class supporting the "Cookie Hunt" feature, including the `gimme` and `sugar` commands."""

    def __init__(self, bot: commands.Bot):
        """Initializes the cog and starts the automated task.

        :param bot: A discord bot instance which will be saved within the class instance.
        """

        super().__init__(bot)

        # Init instance vars
        self.cookie_data = self._parse_cookie_data()
        self.cookie_available = False
        self.cookie_prepared_timestamp = None
        self.cookie_drop_delay_hours = None
        self.cookie_drop_delay_minutes = None
        self.cookie_type = None

    @commands.command()
    async def gimme(self, ctx: commands.Context):
        """The origin point for the `gimme` command. Claims a cookie for the calling user if one has been dropped, and
        resets the points for all if the goal was reached.

        :param ctx: The command context.
        """

        if not self.cookie_available:
            # No cookie available message
            await ctx.send('There is no cookie available right now. Sorry!')
            return

        # Write down the pertinent information for the drop since it's about to get wiped
        cookie_type = self.cookie_type

        # Mark that we got the cookie so no one else takes it (and prepare the next one)
        self._prep_cookie_drop()

        # Find the target's ID
        if cookie_type['target'] == CookieHuntTarget.CLAIMER:
            target_discord_id = ctx.author.id
        elif cookie_type['target'] == CookieHuntTarget.LEADER:
            target_discord_id = DataAccess.get_top_cookie_collectors(1)[0].Discord_Id
        else:
            # Invalid target, just assume it's the claimer
            target_discord_id = ctx.author.id

        # Award points as needed
        db_user_id = DataAccess.find_user_id_by_discord_id(target_discord_id)
        cookie_count = DataAccess.modify_cookie_count(db_user_id, cookie_type['modifier'])

        # check if goal was reached by the claimer
        cookie_goal = ConfiguredCog.config['content']['cookie_hunt_goal']
        if cookie_count >= cookie_goal:
            # announce winner
            await ctx.send(f'Oh my, it looks like {ctx.author.name} is the cookie monster!')

            # Award the role
            winner_role_name = ConfiguredCog.config['content']['cookie_hunt_winner_role']
            role = self.find_role_in_guild(winner_role_name, ctx.guild)
            if role:
                # Remove role from all users
                for member in ctx.guild.members:
                    if role in member.roles:
                        await member.remove_roles(role, reason='No longer the cookie hunt winner.')
                # Give the role to the winner
                if not self.member_contains_role(role.name, ctx.author):
                    await ctx.author.add_roles(role, reason=f'First to grab {cookie_goal} cookies.')

            # reset cookie counts
            DataAccess.reset_all_cookies()
        else:
            # Figure out proper grammar
            if cookie_count == 1:
                cookie_grammar_word = 'cookie'
            else:
                cookie_grammar_word = 'cookies'

            # Send a message saying they got the cookie
            if cookie_type['target'] == CookieHuntTarget.CLAIMER:
                await ctx.send(f'{ctx.author.name} got a {cookie_type["name"]} cookie! '
                               f'They now have {cookie_count} {cookie_grammar_word}.')
            else:
                target_user = self.bot.get_user(int(target_discord_id))
                if target_user:
                    target_user_name = target_user.name
                else:
                    target_user_name = f'Unknown ({target_discord_id})'

                await ctx.send(f'{ctx.author.name} got a {cookie_type["name"]} cookie! '
                               f'The leader, {target_user_name}, now has {cookie_count} {cookie_grammar_word}.')

    @commands.command()
    async def sugar(self, ctx: commands.Context, options: str = None):
        """The origin point for the `sugar` command. Shows relevant cookie count scores based on the options provided.

        :param ctx:     The command context.
        :param options: The (optional) parameters for the sugar command, as enumerated by the
                        `CookieHuntSugarOptions` enumeration.
        """

        if options is not None:
            if options.lower() == CookieHuntSugarOptions.HIGH.value:
                # Get the high scores
                top_collectors = DataAccess.get_top_cookie_collectors(3)

                # convert IDs to nicknames and display them
                collectors_displayed = False
                embed = None
                for Discord_Id, Cookie_Count in top_collectors:
                    if not collectors_displayed:
                        # Only build the embed the first time through the loop
                        embed = Embed(title='Top Cookie Collectors',
                                      color=ConfiguredCog.convert_color('#8a4b38'))

                        collectors_displayed = True

                    discord_user = self.bot.get_user(int(Discord_Id))
                    if discord_user:
                        user_name = discord_user.name
                    else:
                        user_name = f'Unknown ({Discord_Id})'

                    user_name = f'{user_name}:'

                    # Add field
                    embed.add_field(name=user_name, value=Cookie_Count, inline=False)

                if collectors_displayed:
                    # We found collectors to display
                    await ctx.send(embed=embed)
                else:
                    # Our query returned no results
                    await ctx.send('_No one has gotten any cookies yet!_')
            else:
                # Unknown option error
                await ctx.send(f'Unknown command `{options}`, please re-enter your command and try again.')
        else:
            # Find cookie count for the user
            cookie_count = DataAccess.get_cookie_count_by_discord_id(ctx.author.id)

            # Figure out proper grammar
            if cookie_count == 1:
                cookie_word = 'cookie'
            else:
                cookie_word = 'cookies'

            # Give the requesting user's score
            await ctx.send(f'{ctx.author.name} has {cookie_count} {cookie_word}.')

    @commands.command('forcedrop')
    @commands.has_any_role(*ConfiguredCog.config['mod_roles'])
    async def force_drop(self, ctx: commands.Context):
        """Forces a cookie to drop ahead of schedule.

        :param ctx: The command context.
        """

        await self._check_to_send_cookie(True)

    @tasks.loop(minutes=1)
    async def _check_to_send_cookie(self, force_drop: bool = False):
        """A looping task to check if a cookie needs to be sent. Checks a few parameters such as a randomized time
        delay and whether there's already an available cookie to claim. If all the parameters have been met,
        picks a random channel from a configured list and drops a cookie into that channel for claiming.

        :param force_drop:  Overrides any delays and force a cookie to drop immediately.
        """

        # If random number isn't set, plan out a new cookie drop
        if self.cookie_drop_delay_hours is None:
            self._prep_cookie_drop()

        # If current timestamp is after the logged timestamp + random number's hours, then drop a cookie in a
        # random channel from the list of channels (assuming we can find the channels by name)
        time_delta = datetime.now() - self.cookie_prepared_timestamp
        if (force_drop or time_delta > timedelta(hours=self.cookie_drop_delay_hours,
                                                 minutes=self.cookie_drop_delay_minutes)) \
                and not self.cookie_available:
            self.logger.debug('Dropping a cookie.')

            # Build the cookie drop message
            prefix = ConfiguredCog.config['command_prefix']
            color = ConfiguredCog.convert_color('#8a4b38')
            cookie_drop_embed = Embed(color=color, title=':cookie:', description=f'Here, have a cookie! Use '
                                                                                 f'`{prefix}gimme` to take it!')

            # Pick a random channel to send it to
            channel = self._pick_random_channel_to_send()

            if channel is not None:
                self.cookie_available = True

                await channel.send(embed=cookie_drop_embed)
            else:
                self.logger.error('No valid channels were found. Skipping drop.')

    def cog_load(self) -> None:
        """Overridden from commands.Cog; starts the automated task."""

        self._check_to_send_cookie.start()

    def cog_unload(self):
        """Overridden from commands.Cog; stops the automated task."""

        self._check_to_send_cookie.cancel()

    def _prep_cookie_drop(self):
        """Sets up the class's instance variables for a new cookie drop in the future."""

        min_hour = ConfiguredCog.config['content']['cookie_hunt_hour_variance'][0]
        max_hour = ConfiguredCog.config['content']['cookie_hunt_hour_variance'][1]
        hour_delay = randint(min_hour, max_hour)
        minute_delay = randint(0, 59)  # Picks a random minute within the hour to drop it
        cookie_type = choices(self.cookie_data, self._get_cookie_weights())[0]

        self.logger.debug(f'Preparing a cookie drop for about {hour_delay} hours and {minute_delay} minutes from now.'
                          f'It is a {cookie_type["name"]} cookie.')
        self.cookie_available = False
        self.cookie_prepared_timestamp = datetime.now()
        self.cookie_drop_delay_hours = hour_delay
        self.cookie_drop_delay_minutes = minute_delay
        self.cookie_type = cookie_type

    @staticmethod
    def _parse_cookie_data() -> dict:
        """Parses the cookie file out into its corresponding data

        :return:    The parsed json data from the necessary data file
        """

        with open('Data/cookies.json') as cookie_data_file:
            cookie_data_dict = json.load(cookie_data_file)

        # Cast the necessary data
        for cookie_type in cookie_data_dict:
            cookie_type['weight'] = float(cookie_type['weight'])
            cookie_type['target'] = CookieHuntTarget(cookie_type['target'])

        return cookie_data_dict

    def _get_cookie_weights(self) -> list:
        """Gets an arbitrarily ordered list of weights mapped to the cookie data dictionary.

        :return:    A list of weights.
        """
        cookie_weights = []
        for cookie_type in self.cookie_data:
            cookie_weights.append(cookie_type['weight'])

        return cookie_weights

    def _pick_random_channel_to_send(self) -> Optional[TextChannel]:
        """Takes the preconfigured list of available channels that we can drop a cookie into, and returns a possible
        one.

        :return:    The randomly selected channel to send a cookie to, or None if no valid options were found.
        """

        # Shuffle the whole list of all the channels we can access, so that in case we can't find the first channel
        # that we randomly picked, we move on to the next one safely.
        random_channel_pick_list = sample(ConfiguredCog.config['content']['cookie_hunt_allowed_channels'],
                                          len(ConfiguredCog.config['content']['cookie_hunt_allowed_channels']))
        for selected_channel_name in random_channel_pick_list:
            for channel in self.bot.get_all_channels():
                if channel.name == selected_channel_name and isinstance(channel, TextChannel):
                    # Found a channel that matches the name in the config, therefore this is the random channel selected
                    return channel

        # No valid channel options, return None
        return None


class DiceRollerCog(ConfiguredCog):
    """A class supporting discord dice rolling features"""

    @commands.command()
    async def roll(self, ctx: commands.context, dice: str):
        """The origin point for the dice roll command.

        :param ctx:     The command context.
        :param dice:    The dice roll command to parse.
        """

        if dice:
            lexer = DiceLexer()
            parser = DiceParser()

            try:
                step_data, result = parser.parse(lexer.tokenize(dice))
            except TypeError:
                await ctx.send("There was an error with your roll syntax. Please try again.")
                return

            if result.is_integer():
                result = int(result)

            color = ConfiguredCog.convert_color(ConfiguredCog.config['content']['dice_result_embed_color'])
            title = f'Roll for {ctx.author.name}'
            description = f'**Result:**\n' \
                          f'```\n' \
                          f'{result}\n' \
                          f'```\n' \
                          f'**Steps:**\n' \
                          f'```\n'
            for step in step_data:
                description += step + '\n'
            description += '```'

            embed = Embed(color=color, title=title, description=description)

            await ctx.send(embed=embed)

    @commands.command()
    async def r(self, ctx: commands.context, text: str):
        """An alias for the `roll` method.

        :param ctx:     The command context.
        :param text:    The dice roll command to parse.
        """
        return await self.roll(ctx, text)


class AutoDrawingPrompt(ConfiguredCog):
    """A class supporting the Drawing Prompt automatic posting functionality"""

    def __init__(self, bot: commands.Bot):
        """Initializes the cog and starts the automated task

        :param bot: A discord bot instance which will be saved within the class instance.
        """

        super().__init__(bot)
        self.current_prompt = ''

    @commands.Cog.listener()
    async def on_ready(self):
        """Cog Listener to automatically run the task on start."""

        await self._get_sketch_prompt()

    async def cog_load(self):
        """Overridden from commands.Cog; starts the automated task."""

        self._get_sketch_prompt.start()

    def cog_unload(self):
        """Overridden from commands.Cog; stops the automated task."""
        self._get_sketch_prompt.cancel()

    @staticmethod
    def _get_neat_date(date: datetime) -> str:
        """Takes a datetime object and converts the day and month into a cleanly formatted string.

        :param date:    The datetime object to convert to a neat string

        :return:    The formatted month and day in the format `[Month] [Numeric Day][st|nd|rd|th]`
        """
        month_selector = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                          "October", "November", "December"]
        month_string = month_selector[date.month - 1]

        day = date.day

        if day == 1 or day == 21 or day == 31:
            suffix = "st"
        elif day == 2 or day == 22:
            suffix = "nd"
        elif day == 3 or day == 23:
            suffix = "rd"
        else:
            suffix = "th"

        neat_date = f"{month_string} {day}{suffix}"
        return neat_date

    def _get_daily_drawing_prompt(self) -> str:
        """Gets today's drawing prompt from reddit.com/r/SketchDaily, if it exists.

        :return: The daily drawing prompt if there is one found for today; or an empty string if none for today was
        found.
        """

        site = urllib.request.urlopen(
            urllib.request.Request("https://reddit.com/r/SketchDaily/new", headers={'User-Agent': 'Mozilla/5.0'}))
        site_str = site.read().decode('utf-8')

        # search for today's theme on the skd site
        now = datetime.now()
        neat_today_date = self._get_neat_date(now)
        loc = site_str.find(neat_today_date + " - ")

        # if we can't find today's theme, return a blank string
        if loc == -1:
            return ''
            # FIND YESTERDAY'S THEME:
            # yesterday = datetime.now() - timedelta(days=1)
            # neat_today_date = self._get_neat_date(yesterday)
            # loc = site_str.find(neat_today_date + " - ")

        site_str = site_str[loc:]
        site_str = site_str[:site_str.find('"')]
        if len(site_str) > 100:
            site_str = site_str[:100]

        return site_str

    @tasks.loop(minutes=30)
    async def _get_sketch_prompt(self):
        """A looping task to query the web for today's sketch prompt and announce it in a given discord channel if it
        was found. If today's prompt was already announced, or if the prompt for today wasn't found, nothing is
        announced in the channel.
        """

        drawing_prompt = self._get_daily_drawing_prompt()

        if drawing_prompt == '':
            # No drawing prompt found for today; don't do anything
            return
        elif not drawing_prompt == self.current_prompt:
            # The prompt we pulled does not match what we found before, so post the new text.
            for channel in self.bot.get_all_channels():
                if channel.name == ConfiguredCog.config['content']['daily_prompt_channel'] \
                        and isinstance(channel, TextChannel):
                    # Build the prompt message
                    color = ConfiguredCog.convert_color(ConfiguredCog.config['content']['prompt_color'])
                    title = 'Prompt for today, courtesy of r/SketchDaily'
                    url = 'https://reddit.com/r/SketchDaily'
                    description = drawing_prompt
                    message = Embed(color=color, title=title, url=url, description=description)

                    # Send the message
                    await channel.send(embed=message)

                    # Note down that we found today's prompt (so as not to re-send it)
                    self.current_prompt = drawing_prompt

                    break
