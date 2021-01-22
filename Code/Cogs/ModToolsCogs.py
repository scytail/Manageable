import urllib.request
from enum import Enum
from datetime import datetime, timedelta
from discord import Member, Embed
from discord.ext import commands, tasks
from Code.Cogs.Base import ConfiguredCog
from Code.Data import DataAccess


class WarnAction(Enum):
    """An enumeration class containing all the possible warning actions that can be taken."""

    APPLY = 'apply'  # create a warning for a user
    RESOLVE = 'resolve'  # remove oldest warning
    UNDO = 'undo'  # remove newest warning
    VIEW = 'view'  # display warning count


class UserWarnCog(ConfiguredCog):
    """A class supporting the warning functionality

    Methods
    -------
    warn    The origin point for the `warn` command.
    """

    @commands.command()
    @commands.has_any_role(*ConfiguredCog.config['mod_roles'])
    async def warn(self, ctx: commands.Context, action: str, *user_name_list: str):
        """The origin point for the `warn` command.

        Parameters
        ----------
        ctx:            discord.ext.commands.Context    The command context.
        action:         str                             The string action to execute. Should correlate to an action in
                                                        the `WarnAction` enumeration.
        user_name_list: List[str]                       A list of strings, denoting either a user's nickname, or their
                                                        discord ID. This list will be joined by spaces and compared
                                                        against the server's member list, first by trying to convert it
                                                        to an integer and searching by unique ID, then by querying the
                                                        list of nicknames by the joined string.
        """

        # join all the arguments after the action together, in case we are looking for a display name that has a space
        user_name_query = ' '.join(user_name_list)
        action = action.lower()

        # Finds all the members that match the query (either a discord ID or a display name)
        member_matches = self._find_discord_member(user_name_query)

        if not member_matches:
            await ctx.send(f'No user by the name or id of `{user_name_query}` could be found. '
                           f'Please check your spelling and try again.')

        elif len(member_matches) > 1:
            await ctx.send(self._multi_member_found_message(user_name_query, member_matches))

        else:
            target_member = member_matches[0]

            # remove outdated warnings for the found user
            self._remove_outdated_warnings(target_member)

            if action == WarnAction.APPLY.value:
                warning_count = self._warn_member(target_member)
                message = f'The user "{user_name_query}" has now been warned, for a total of {warning_count} times.'
            elif action == WarnAction.RESOLVE.value or \
                    action == WarnAction.UNDO.value:
                warning_count = self._remove_warning(target_member, action)
                message = f'The user "{user_name_query}" has now been unwarned, they now have {warning_count} warnings.'
            elif action == WarnAction.VIEW.value:
                warning_count = self._view_user_warnings(target_member)
                message = f'The user "{user_name_query}" has {warning_count} warnings.'
            else:
                message = f'Unknown warning command `{action}`, please re-enter your command and try again.'

            await ctx.send(message)

    def _remove_outdated_warnings(self, target_member: Member):
        """Queries the database for warnings pertaining to the specified member and deletes ones that are outdated.

        Parameters
        ----------
        target_member:  discord.Member  The member to look for when removing outdated warnings.
        """

        warning_duration = self.config['warning_duration_days']

        if warning_duration <= 0:
            # If duration set in the config is zero or less, we assume warnings are permanent.
            return

        user_warnings = DataAccess.lookup_warnings_by_discord_id(target_member.id)

        for warning in user_warnings:
            if warning is not None and datetime.now() - timedelta(days=warning_duration) > warning.Warning_Stamp:
                DataAccess.delete_warning(warning.Warning_Id)

    @staticmethod
    def _warn_member(target_member: Member) -> int:
        """Saves a new warning in the database for the member specified.

        Please note that this method will add a member row to the database if it cannot find one, before continuing
        onwards to add a warning to that member.

        Parameters
        ----------
        target_member:  discord.Member  The member to add a warning to.

        Returns
        -------
        int     The number of total warnings assigned to the member.
        """

        warning_count = DataAccess.lookup_warnings_by_discord_id(target_member.id).count()

        # Find the user in the db so we can attach a warning to it (should add a user if none found)
        db_user_id = DataAccess.find_user_id_by_discord_id(target_member.id)

        # Add the new warning
        DataAccess.add_warning(db_user_id)
        warning_count += 1

        return warning_count

    @staticmethod
    def _remove_warning(target_member: Member, action: str) -> int:
        """Deletes a warning in the database for the member specified.

        Parameters
        ----------
        target_member:  discord.Member  The member to add a warning to.
        action:         str             The action to perform. MUST be either `WarnAction.RESOLVE` or `WarnAction.UNDO`.

        Returns
        -------
        int     The number of total warnings assigned to the member.

        Exceptions
        ----------
        ValueError  When the action argument is not a valid string.
        """

        user_warnings = DataAccess.lookup_warnings_by_discord_id(target_member.id)

        warning_count = user_warnings.count()

        if warning_count == 0:
            # no warnings, so nothing to remove.
            return warning_count

        if action == WarnAction.RESOLVE.value:
            # Remove the oldest index
            delete_newest = False
        elif action == WarnAction.UNDO.value:
            # Remove the newest index
            delete_newest = True
        else:
            raise ValueError('The action argument must be a valid removal WarnAction.')

        DataAccess.delete_warning_by_discord_id(target_member.id, delete_newest)
        warning_count -= 1

        return warning_count

    @staticmethod
    def _view_user_warnings(target_member: Member) -> int:
        """Finds the number of warnings in the database for the member specified.

        Parameters
        ----------
        target_member:  discord.Member  The member to add a warning to.

        Returns
        -------
        int     The number of total warnings assigned to the member.
        """

        warning_rows = DataAccess.lookup_warnings_by_discord_id(target_member.id)

        if warning_rows.first() is None:
            count = 0
        else:
            count = warning_rows.count()

        return count

    def _find_discord_member(self, user_query: str) -> list:
        """Finds the discord information for the users matching the provided query.

        This method will attempt to convert the query into an integer and grab the user via the id first. If that fails,
        it will take the raw string provided and attempt to find all users with the matching nickname. In the event that
        it finds more than member that matches the query, it will return all of them.

        Parameters
        ----------
        user_query: str     The query to search for, either an integer discord ID or a member nickname.

        Returns
        -------
        list    A list of `discord.Member` instances, each one relating to a member that matched the query, or an
                empty list, if no matches were found.
        """
        member_matches = []

        # try to lookup by ID first, as it'll be faster
        try:
            member_matches.append(self.bot.get_user(int(user_query)))
        except ValueError:
            # couldn't cast the user to an integer, so ignore that type of error.
            pass

        # couldn't find by ID, attempt to look up by display name
        if not member_matches:
            member_matches = []
            for member in self.bot.get_all_members():
                member_already_in_match_list = False
                if member.display_name.upper() == user_query.upper() or \
                        (member.nick is not None and member.nick.upper() == user_query.upper()) or \
                        member.name.upper() == user_query.upper():
                    # Only add a member if the ID (which is unique to a discord user) isn't already in the list
                    for member_match in member_matches:
                        if member.id == member_match.id:
                            member_already_in_match_list = True
                            break
                    if not member_already_in_match_list:
                        member_matches.append(member)

        return member_matches

    @staticmethod
    def _multi_member_found_message(user_search_query: str, member_matches: list) -> str:
        """Builds a message listing out all members found with the user search query provided.

        Parameters
        ----------
        user_search_query:  str     The search query that was used to find all the members listed.
        member_matches:     list    A list of `discord.Member` instances, each relating to a member that matched the
                                    search query.

        Returns
        -------
        str     A user-friendly error message reporting all the matches found with the given error message.
        """

        multiple_found_message = f'Multiple users by the identifier "{user_search_query}" were found. Displaying as\n'
        multiple_found_message += f'*<display name>* (*<account name>*), **id:** *<id>*:\n\n'

        for member in member_matches:
            uid = member.id
            name = member.name
            display_name = member.display_name
            multiple_found_message += f'- {display_name} ({name}), **id:** {uid}\n'

        multiple_found_message += f'\nPlease try again, using the unique id for the user you wish to warn.'

        return multiple_found_message


class AutoDrawingPrompt(ConfiguredCog):
    """A class supporting the Drawing Prompt automatic posting functionality

        Methods
        -------
        __init__    Overridden method from base class to set up and start the automated task
        cog_unload  Overridden method from commands.Cog to stop the task
        """

    def __init__(self, bot: commands.Bot):
        """Initializes the cog and starts the automated task

        Parameters
        ----------
        bot:    discord.ext.commands.Bot    A discord bot instance which will be saved within the class instance.
        """

        super().__init__(bot)
        self.current_prompt = ''

        # Start the task
        self._get_sketch_prompt.start()

    @commands.Cog.listener()
    async def on_ready(self):
        # Run the task so that we aren't waiting for the task
        await self._get_sketch_prompt()

    def cog_unload(self):
        """Overridden from commands.Cog; stops the automated task."""
        self._get_sketch_prompt.cancel()

    @staticmethod
    def _get_neat_date(date: datetime) -> str:
        """Takes a datetime object and converts the day and month into a cleanly formatted string.

        Parameters
        ----------
        date:   datetime    The datetime object to convert to a neat string

        Returns
        -------
        str     The formatted month and day in the format `[Month] [Numeric Day][st|nd|er]`
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

        Returns
        -------
        str     The daily drawing prompt if there is one found for today; or an empty string if none for today was found
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
        site_str = site_str[:site_str.find('<')]
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
                if channel.name == ConfiguredCog.config['content']['daily_prompt_channel']:
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

