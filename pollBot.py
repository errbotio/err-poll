# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from errbot.utils import drawbar
from errbot import botcmd, BotPlugin

# The polls are stored in the shelf. The root of the shelf is a dictionary, where K = name of the poll and V = the poll data.
# This data itself is a tuple of a dictionary and a list: ({}, [])
#   In this dictionary the keys are the poll options and the values are the number of votes.
#   The list stores the names of the users who already voted.


class PollBot(BotPlugin):

    min_err_version = '2.2.0-beta' # it needs split_args
    active_poll = None

    @botcmd
    def poll(self, mess, args):
        """List all polls."""
        return self.poll_list(mess, args)

    @botcmd
    def poll_new(self, mess, args):
        """Create a new poll."""
        title = args

        if not title:
            return 'usage: !poll new <poll_title>'

        if title in self:
            return 'A poll with that title already exists.'

        poll = ({}, [])
        self[title] = poll

        if not PollBot.active_poll:
            PollBot.active_poll = title

        return 'Poll created. Use !poll option to add options.'

    @botcmd
    def poll_remove(self, mess, args):
        """Remove a poll."""
        title = args

        if not title:
            return 'usage: !poll remove <poll_title>'

        try:
            del self[title]
            return 'Poll removed.'
        except KeyError as _:
            return 'That poll does not exist. Use !poll list to see all polls.'

    @botcmd
    def poll_list(self, mess, args):
        """List all polls."""
        if len(self) > 0:
            return 'All Polls:\n' + u'\n'.join([title + (u' *' if title == PollBot.active_poll else u'') for title in self])
        else:
            return 'No polls found. Use !poll new to add one.'

    @botcmd
    def poll_start(self, mess, args):
        """Start a saved poll."""
        if PollBot.active_poll is not None:
            return '"%s" is currently running, use !poll stop to finish it.' % PollBot.active_poll

        title = args

        if not title:
            return 'usage: !poll start <poll_title>'

        if not title in self:
            return 'Poll not found. Use !poll list to see all polls.'

        self.reset_poll(title)
        PollBot.active_poll = title

        return self.format_poll(title)

    @botcmd
    def poll_stop(self, mess, args):
        """Stop the currently running poll."""
        result = 'Poll finished, final results:\n'
        result += self.format_poll(PollBot.active_poll)

        self.reset_poll(PollBot.active_poll)
        PollBot.active_poll = None

        return result

    @botcmd
    def poll_addoption(self, mess, args):
        """Add an option to the currently running poll."""
        option = args

        if not PollBot.active_poll:
            return 'No active poll. Use !poll start to start a poll.'

        if not option:
            return 'usage: !poll option add <poll_option>'

        poll = self[PollBot.active_poll]
        options, usernames = poll

        if option in options:
            return 'Option already exists. Use !poll show to see all options.'

        options[option] = 0
        self[PollBot.active_poll] = poll

        return self.format_poll(PollBot.active_poll)

    @botcmd
    def poll_show(self, mess, args):
        """Show the currently running poll."""
        if not PollBot.active_poll:
            return 'No active poll. Use !poll start to start a poll.'

        return self.format_poll(PollBot.active_poll)

    @botcmd
    def poll_vote(self, mess, args):
        """Vote for the currently running poll."""
        if not PollBot.active_poll:
            return 'No active poll. Use !poll start to start a poll.'

        index = args

        if not index:
            return 'usage: !poll vote <option_number>'

        if not index.isdigit():
            return 'Please vote using the numerical index of the option.'

        poll = self[PollBot.active_poll]
        options, usernames = poll

        index = int(index)
        if index > len(options) or index < 1:
            return 'Please choose a number between 1 and %d (inclusive).' % len(options)

        option = list(options.keys())[index - 1]  # FIXME: this looks random

        if not option in options:
            return 'Option not found. Use !poll show to see all options of the current poll.'

        username = mess.frm.stripped

        if username in usernames:
            return 'You have already voted.'

        usernames.append(username)

        options[option] += 1
        self[PollBot.active_poll] = poll

        return self.format_poll(PollBot.active_poll)

    def format_poll(self, title):
        poll = self[title]
        options, usernames = poll

        total_votes = sum(options.values())

        result = PollBot.active_poll + '\n'
        index = 1
        for option in options:
            result += '%s %d. %s (%d votes)\n' % (drawbar(poll[0][option], total_votes), index, option, poll[0][option])
            index += 1

        return result.strip()

    def reset_poll(self, title):
        poll = self[title]

        options, usernames = poll

        for option in options:
            options[option] = 0

        del usernames[:]

        self[title] = poll
