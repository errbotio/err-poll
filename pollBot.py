# -*- coding: utf-8 -*-
from errbot.botplugin import BotPlugin
from errbot.jabberbot import botcmd
from errbot.utils import get_jid_from_message, drawbar

# The polls are stored in the shelf. The root of the shelf is a dictionary, where K = name of the poll and V = the poll data.
# This data itself is a tuple of a dictionary and a list: ({}, [])
#   In this dictionary the keys are the poll options and the values are the number of votes.
#   The list stores the names of the users who already voted.


class PollBot(BotPlugin):

    active_poll = None

    @botcmd
    def poll(self, mess, args):
        """List all polls."""
        return self.poll_list(mess, args)

    @botcmd
    def poll_new(self, mess, args):
        """Create a new poll."""
        title = args.strip()

        if not title:
            return u'usage: !poll new <poll_title>'

        if title in self.shelf:
            return u'A poll with that title already exists.'

        poll = ({}, [])
        self.shelf[title] = poll

        if not PollBot.active_poll:
            PollBot.active_poll = title

        return u'Poll created. Use !poll option to add options.'

    @botcmd
    def poll_remove(self, mess, args):
        """Remove a poll."""
        title = args.strip()

        if not title:
            return u'usage: !poll remove <poll_title>'

        try:
            del self.shelf[title]
            return u'Poll removed.'
        except KeyError:
            return u'That poll does not exist. Use !poll list to see all polls.'

    @botcmd
    def poll_list(self, mess, args):
        """List all polls."""
        if len(self.shelf) > 0:
            return u'All Polls:\n' + u'\n'.join([title + (u' *' if title == PollBot.active_poll else u'') for title in self.shelf])
        else:
            return u'No polls found. Use !poll new to add one.'

    @botcmd
    def poll_start(self, mess, args):
        """Start a saved poll."""
        if PollBot.active_poll is not None:
            return u'"%s" is currently running, use !poll stop to finish it.' % PollBot.active_poll

        title = args.strip()

        if not title:
            return u'usage: !poll start <poll_title>'

        if not title in self.shelf:
            return u'Poll not found. Use !poll list to see all polls.'

        self.reset_poll(title)
        PollBot.active_poll = title

        return self.format_poll(title)

    @botcmd
    def poll_stop(self, mess, args):
        """Stop the currently running poll."""
        result = u'Poll finished, final results:\n'
        result += self.format_poll(PollBot.active_poll)

        self.reset_poll(PollBot.active_poll)
        PollBot.active_poll = None

        return result

    @botcmd
    def poll_addoption(self, mess, args):
        """Add an option to the currently running poll."""
        option = args.strip()

        if not PollBot.active_poll:
            return u'No active poll. Use !poll start to start a poll.'

        if not option:
            return u'usage: !poll option add <poll_option>'

        poll = self.shelf[PollBot.active_poll]

        if option in poll[0]:
            return u'Option already exists. Use !poll show to see all options.'

        poll[0][option] = 0
        self.shelf[PollBot.active_poll] = poll

        return self.format_poll(PollBot.active_poll)
        #return u'Added \'%s\' to poll.' % option

    @botcmd
    def poll_show(self, mess, args):
        """Show the currently running poll."""
        if not PollBot.active_poll:
            return u'No active poll. Use !poll start to start a poll.'

        return self.format_poll(PollBot.active_poll)

    @botcmd
    def poll_vote(self, mess, args):
        """Vote for the currently running poll."""
        if not PollBot.active_poll:
            return u'No active poll. Use !poll start to start a poll.'

        index = args.strip()

        if not index:
            return u'usage: !poll vote <option_number>'

        if not index.isdigit():
            return u'Please vote using the numerical index of the option.'

        poll = self.shelf[PollBot.active_poll]
        options = poll[0]

        index = int(index)
        if index > len(options) or index < 1:
            return u'Please choose a number between 1 and %d (inclusive).' % len(options)

        option = options.keys()[index - 1]

        if not option in options:
            return u'Option not found. Use !poll show to see all options of the current poll.'

        usernames = poll[1]
        username = get_jid_from_message(mess)

        if username in usernames:
            return u'You have already voted.'

        usernames.append(username)

        options[option] += 1
        self.shelf[PollBot.active_poll] = poll

        return self.format_poll(PollBot.active_poll)

    def format_poll(self, title):
        poll = self.shelf[title]

        total_votes = sum(poll[0].values())

        result = PollBot.active_poll + u'\n'
        index = 1
        for option in poll[0]:
            result += u'%s %d. %s (%d votes)\n' % (drawbar(poll[0][option], total_votes), index, option, poll[0][option])
            index += 1

        return result.strip()

    def reset_poll(self, title):
        poll = self.shelf[title]

        options = poll[0]
        usernames = poll[1]

        for option in options.iterkeys():
            options[option] = 0

        del usernames[:]

        self.shelf[title] = poll
