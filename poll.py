from typing import List, Mapping

from errbot.backends.base import Identifier
from errbot import botcmd, BotPlugin

BAR_WIDTH = 15.0


def drawbar(value, max_):
    if max_:
        value_in_chr = int(round((value * BAR_WIDTH / max_)))
    else:
        value_in_chr = 0
    return '[' + '█' * value_in_chr + '▒' * int(round(BAR_WIDTH - value_in_chr)) + ']'


class PollEntry(object):
    """
    This is just a data object that can be pickled.
    """
    def __init__(self):
        self._options = {}
        self._has_voted = []

    @property
    def options(self) -> Mapping[str, int]:
        return self._options

    @property
    def has_voted(self) -> List[Identifier]:
        return self._has_voted

    def __str__(self) -> str:
        total_votes = sum(self._options.values())

        result = ''
        keys = sorted(self._options.keys())
        for index, option in enumerate(keys):
            votes = self._options[option]
            result += '%s %d. %s (%d votes)\n' % (drawbar(votes, total_votes), index+1, option, votes)

        return result.strip()


class Poll(BotPlugin):

    def activate(self):
        super().activate()

        # initial setup
        if 'current_poll' not in self:
            self['current_poll'] = None
        if 'polls' not in self:
            self['polls'] = {}

    @botcmd
    def poll_new(self, _, title):
        """Create a new poll.
        usage: !poll new <poll_title>
        """
        if not title:
            return 'usage: !poll new <poll_title>'

        if title in self['polls']:
            return 'A poll with that title already exists.'

        with self.mutable('polls') as polls:
            polls[title] = PollEntry()

        if not self['current_poll']:
            self['current_poll'] = title

        return 'Poll created. Use !poll option to add options.'

    @botcmd
    def poll_remove(self, _, title):
        """Remove a poll."""
        if not title:
            return 'usage: !poll remove <poll_title>'

        with self.mutable('polls') as polls:
            try:
                del polls[title]
            except KeyError as _:
                return 'That poll does not exist. Use !poll list to see all polls.'
        return 'Poll removed.'

    @botcmd
    def poll_list(self, mess, args):
        """List all polls."""
        if self['polls']:
            return 'All Polls:\n' + \
                   '\n'.join([title + (' *' if title == self['current_poll'] else '') for title in self['polls']])
        return 'No polls found. Use !poll new to add one.'

    @botcmd
    def poll_start(self, _, title):
        """Start a saved poll."""
        if self['current_poll']:
            return '"%s" is currently running, use !poll end to finish it.' % self['current_poll']

        if not title:
            return 'usage: !poll start <poll_title>'

        if title not in self['polls']:
            return 'Poll not found. Use !poll list to see all polls.'

        self.reset_poll(title)
        self['current_poll'] = title

        return '%s:\n%s' % (title, str(self['polls'][title]))

    @botcmd
    def poll_end(self, _, args):
        """Stop the currently running poll."""
        current_poll = self['current_poll']
        if not current_poll:
            return 'There is no active Poll.'

        result = 'Poll finished, final results:\n'
        result += str(self['polls'][current_poll])

        self.reset_poll(current_poll)
        self['current_poll'] = None
        return result

    @botcmd
    def poll_option(self, _, option):
        """Add an option to the currently running poll."""
        current_poll = self['current_poll']
        if not current_poll:
            return 'No active poll. Use !poll start to start a poll.'

        if not option:
            return 'usage: !poll option <poll_option>'

        with self.mutable('polls') as polls:
            poll = polls[current_poll]

            if option in poll.options:
                return 'Option already exists. Use !poll show to see all options.'

            poll.options[option] = 0

            return '%s:\n%s' % (current_poll, str(poll))

    @botcmd
    def poll(self, _, args):
        """Show the currently running poll."""
        current_poll = self['current_poll']

        if not current_poll:
            return 'No active poll. Use !poll start to start a poll.'

        return '%s:\n%s' % (current_poll, str(self['polls'][current_poll]))

    @botcmd
    def vote(self, msg, index):
        """Vote for the currently running poll."""
        current_poll = self['current_poll']
        if not current_poll:
            return 'No active poll. Use !poll start to start a poll.'

        if not index:
            return 'usage: !vote <option_number>'

        if not index.isdigit():
            return 'Please vote using the numerical index of the option.'

        with self.mutable('polls') as polls:
            poll = polls[current_poll]
            index = int(index)
            if index > len(poll.options) or index < 1:
                return 'Please choose a number between 1 and %d (inclusive).' % len(poll.options)

            option = sorted(poll.options.keys())[index - 1]

            if option not in poll.options:
                return 'Option not found. Use !poll show to see all options of the current poll.'

            if msg.frm in poll.has_voted:
                return 'You have already voted.'

            poll.has_voted.append(msg.frm)

            poll.options[option] += 1

            return '%s:\n%s' % (current_poll, str(poll))

    def reset_poll(self, title):
        with self.mutable('polls') as polls:
            poll = polls[title]
            for option in poll.options:
                poll.options[option] = 0
            del poll.has_voted[:]