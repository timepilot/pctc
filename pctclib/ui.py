# pctc: python curses twitter client

import urwid
import re

class Tweet(urwid.Text):
    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

class UI(object):
    palette = [
            ('header', 'light green', 'dark blue'),
            ('footer', 'header'),
            ('bg', 'white', 'dark gray'),
            ('in focus', 'dark gray', 'white'),
        ]

    def __init__(self, twitobj):
        self.twitobj = twitobj

        header = urwid.Text("Welcome to PCTC. Logged in as %s (@%s)." %
                                            (twitobj.name, twitobj.username))
        header = urwid.AttrMap(header, 'header')

        self.replies = self._wrap_statuses(twitobj.get_replies())
        self.updates = self._wrap_statuses(twitobj.get_updates())
        self.columns = urwid.Columns([self.updates, self.replies], dividechars=2)

        self.footer = urwid.AttrMap(urwid.Edit("Tweet: "), 'footer')

        self.frame = urwid.Frame(self.columns, header, self.footer, focus_part='footer')
        self.focussed = 'footer'
        wrapped = urwid.AttrMap(self.frame, 'bg')
        loop = urwid.MainLoop(wrapped, UI.palette, unhandled_input=self.handle)
        loop.set_alarm_in(300, self.wrapped_refresh)
        try:
            loop.run()
        except KeyboardInterrupt:
            print "Keyboard interrupt received, quitting gracefully"
            raise urwid.ExitMainLoop

    def _wrap_statuses(self, statuses):
        textlist = map(Tweet, statuses)
        walker = urwid.SimpleListWalker([
                urwid.AttrMap(w, None, 'in focus') for w in textlist
            ])
        return urwid.ListBox(walker)

    def handle(self, keys):
        methdict = {
                'tab'   : self.change_focus,
                'enter' : self.post,
                'f5'    : self.refresh,
                'home'  : lambda: self.scroll('home'),
                'end'   : lambda: self.scroll('end'),
                'r'     : self.reply,
            }
        try:
            methdict[keys]()
        except KeyError:
            pass

    def change_focus(self):
        if self.focussed == 'footer':
            self.frame.set_focus('body')
            self.focussed = 'body'
        elif self.focussed == 'body':
            self.frame.set_focus('footer')
            self.focussed = 'footer'

    def post(self):
        edit = self.footer.original_widget
        text = edit.get_edit_text()
        edit.set_edit_text('')
        if len(text) < 140:
            self.twitobj.post(text)

    def refresh(self):
        for category in ('replies', 'updates'):
            walker = getattr(self, category).body
            statuses = getattr(self.twitobj, 'get_%s' % category)()
            statuses = map(urwid.Text, statuses)
            statuses = [urwid.AttrMap(s, None, ('in focus')) for s in statuses]
            walker[:] = statuses

    def scroll(self, key):
        widget = self.columns.get_focus()
        if key == "home":
            widget.set_focus(0)
        elif key == "end":
            widget.set_focus(len(widget.body))

    def reply(self):
        listbox = self.columns.get_focus()
        tweet, pos = listbox.get_focus()
        tweettext = tweet.original_widget.text
        edit = self.footer.original_widget
        matches = re.findall(r'@\w+', tweettext)
        edit.insert_text(matches[-1])
        edit.insert_text(' ')
        self.frame.set_focus('footer')

    def wrapped_refresh(self, loop, *args):
        self.refresh()
        loop.set_alarm_in(300, self.wrapped_refresh)
