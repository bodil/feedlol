#!/usr/bin/env python
#
# Copyright 2008 Bodil Stokke <bodil@bodil.tv>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtCore import SIGNAL, QObject, QUrl
from feedlol.FriendFeedAPI import FriendFeedAPI
from feedlol.Notification import NotificationServer
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from routes import Mapper
import cgi, os, re, time, datetime

class QueryData(object):
    def __init__(self, query):
        self._query = query
        self._data = cgi.parse_qs(query)
    
    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            data = object.__getattribute__(self, "_data")
            if key in data:
                return data[key][0]
            raise AttributeError, key

    def __contains__(self, key):
        return key in self._data
    
    def values(self, key):
        return self._data[key]
    
    def getdefault(self, key, default):
        return (key in self) and self._data[key][0] or default
    
    def __repr__(self):
        return "QueryData(" + `self._query` + ")"
    
    def __str__(self):
        return `self._data`

class Request(object):
    def __init__(self, path, query, session = None, ff = None):
        self.path = path
        self.query = QueryData(query)
        self.session = session
        self.ff = ff

class Response(object):
    def __init__(self, template, context = {}, statusCode = 200):
        self.template = template
        self.context = context
        self.statusCode = statusCode

class ErrorResponse(object):
    def __init__(self, statusCode, message):
        self.statusCode = statusCode
        self.message = message

class RedirectResponse(object):
    def __init__(self, url):
        self.redirectUrl = QUrl(url)
        self.statusCode = 301

class DeferredResponse(QObject):
    def __init__(self, deferred, callback, errorCallback):
        QObject.__init__(self, None)
        self.deferred = deferred
        self.callback = callback
        self.errorCallback = errorCallback
    
    def defer(self, server, url, view, request, args):
        self.server = server
        self.url = url
        self.view = view
        self.request = request
        self.args = args
        self.connect(self.deferred, SIGNAL("error"), self.error)
        self.connect(self.deferred, SIGNAL("ready"), self.ready)
    
    def ready(self, data):
        self.args["data"] = data
        response = self.callback(self.request, **self.args)
        self.server._processResponse(self.url, self.view, response, self.request, self.args)
        self.emit(SIGNAL("complete"), self)
    
    def error(self, error):
        self.args["error"] = error
        response = self.errorCallback(self.request, **self.args)
        self.server._processResponse(self.url, self.view, response, self.request, self.args)
        self.emit(SIGNAL("complete"), self)

class Session(object):
    def __init__(self):
        self.user = ""
        self.remoteKey = None
    
    def is_auth(self):
        return self.user and True or False
    
    def logout(self):
        self.user = ""
    
def filter_likes(entry, user):
    for like in entry["likes"]:
        if like["user"]["nickname"] == user:
            return True
    return False

twitterAtRe = re.compile(r"@([A-Za-z0-9_]+)")
def filter_twitterise(value):
    value = twitterAtRe.sub(r'@<a href="http://twitter.com/\1">\1</a>', value)
    return value

def timesince(d, now=None):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    def ungettext(singular, plural, count):
        return (count == 1) and singular or plural
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n))
    )
    # Convert datetime.date to datetime.datetime for comparison
    if d.__class__ is not datetime.datetime:
        d = datetime.datetime(d.year, d.month, d.day)
    if now:
        t = now.timetuple()
    else:
        t = time.gmtime()
    now = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5])

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 minutes'
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = u'%(number)d %(type)s' % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += u', %(number)d %(type)s' % {'number': count2, 'type': name2(count2)}
    return s

def filter_timesince(value):
    return timesince(value)

class SiteServer(QObject):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        self.jinja = Environment(loader = FileSystemLoader("data/templates"), autoescape = True)
        self.jinja.filters["likes"] = filter_likes
        self.jinja.filters["twitterise"] = filter_twitterise
        self.jinja.filters["timesince"] = filter_timesince

        self.mapper = Mapper()
        self.mapper.connect("/", controller = "LolViews", action = "feed")
        self.mapper.connect("/login", controller = "LolViews", action = "login")
        self.mapper.connect("/user/:user", controller = "LolViews", action = "feed")

        self.notes = NotificationServer()

        from PyQt4.QtCore import QSettings
        settings = QSettings()
        if settings.contains("session"):
            from cPickle import loads
            self.session = loads(str(settings.value("session").toString()))
        else:
            self.session = Session()

        self.ff = FriendFeedAPI(self.session)
        
        self.deferredResponses = set()

    def _cleanupDeferred(self, deferred):
        self.deferredResponses.remove(deferred)

    def request(self, url, view):
        url = QUrl(url) # Make a copy, C++ object might no longer exist by the time a deferred response completes
        response, request, args = self._mapRequest(url)
        self._processResponse(url, view, response, request, args)

    def _mapRequest(self, url):
        path = str(url.path())
        query = str(url.encodedQuery())
        print "Request:", path + (query and ("?" + query) or "")
        r = self.mapper.match(path)
        if not r:
            return ErrorResponse(404, "<h1>404 Not Found</h1><p><a href=\"http://www.google.com/\">Try Google</a>.</p>")
        request = Request(path, query, session = self.session, ff = self.ff) #@UnusedVariable
        controller = r["controller"]
        action = r["action"]
        del r["controller"]
        del r["action"]
        exec("from %s import %s" % (controller, action))
        exec("response = %s(request, **r)" % action)
        return response, request, r #@UndefinedVariable

    def _processResponse(self, url, view, response, request, args):
        if isinstance(response, DeferredResponse):
            self.deferredResponses.add(response)
            self.connect(response, SIGNAL("complete"), self._cleanupDeferred)
            response.defer(self, url, view, request, args)
        elif isinstance(response, RedirectResponse):
            self.request(response.redirectUrl, view)
        elif isinstance(response, ErrorResponse):
            view.setHtml(response.message, url)
        else:
            template = self.jinja.get_template(response.template, globals = {
                "session": self.session,
                "media": str(QUrl.fromLocalFile(os.path.join(os.getcwd(), "data", "media")).toEncoded()),
            })
            view.setHtml(template.render(response.context), url)

