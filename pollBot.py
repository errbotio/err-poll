# -*- coding: utf-8 -*-
import os
import shelve
from botplugin import BotPlugin
from jabberbot import botcmd
from utils import get_jid_from_message, drawbar

__author__ = 'gbin'
Q = 'question'
A = 'answers'
V = 'votes'

class PollBot(BotPlugin):

    def format_poll(self):
        title = u'\n' + self.shelf[Q] + u'\n\n'

        results = {}
        m = 0
        for user, answer in self.shelf[V].iteritems():
            nb = results.get(answer, 0)
            results[answer] = nb + 1
            m += 1

        questions_results = map(lambda answer: u'%s %i. %s [%i]' % (drawbar(results.get(answer[0], 0), m),  answer[0], answer[1], results.get(answer[0], 0))
                                , self.shelf[A].iteritems())

        return  title + u'\n'.join(questions_results) + u'\n'

    @botcmd
    def newpoll(self, mess, args):
        """ Start a new poll
        !newpoll Where do you want to eat today ?
        """
        if self.shelf.has_key(Q):
            return 'A poll is currently running, please end it first with !endpoll before [%s]' % self.shelf[
                                                                                                       Q]
        self.shelf.clear()
        self.shelf[Q] = args.strip()
        self.shelf[A] = {}
        self.shelf[V] = {}
        return 'Poll created, use !polloption to add options to it'

    @botcmd
    def polloption(self, mess, args):
        """ Add a poll option to the currently running poll
        !polloption Drunkun Guy
        """
        if not self.shelf.has_key(Q):
            return 'No poll is running now'
        answers = self.shelf[A]
        option = args.strip()
        if option in answers.values():
            return 'This option already exists'
        if answers:
            m = max(answers.keys())
        else:
            m = 0
        answers[m + 1] = option
        self.shelf[A] = answers
        return self.format_poll()

    @botcmd
    def poll(self, mess, args):
        """ display the currently running poll
         !poll
        """
        if not self.shelf.has_key(Q):
            return '\n\nNo poll is running now'
        return self.format_poll()

    @botcmd
    def vote(self, mess, args):
        """ vote for you favorite option in the poll
        !vote 1
        """
        if not self.shelf.has_key(Q):
            return 'No poll is running now'
        votes = self.shelf[V]
        answers = self.shelf[A]
        args = args.strip()
        username = get_jid_from_message(mess)
        if votes.has_key(username):
            return 'You have already voted for [%s]' % answers[votes[username]]
        if not args.isdigit():
            return 'You must vote with digits'
        if not answers.has_key(int(args)):
            return 'There is no voting option [%s]' % args
        votes[username] = int(args)
        self.shelf[V] = votes
        return 'à voté !'

    @botcmd
    def endpoll(self, mess, args):
        """ Show results and End poll
        """
        if not self.shelf.has_key(Q):
            return 'No poll is running now'
        res = self.format_poll()
        self.shelf.clear()
        return '\nFinal results !\n\n' + res
