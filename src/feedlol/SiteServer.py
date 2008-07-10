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

from PyQt4.QtCore import QUrl
from feedlol.Notification import NotificationServer
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from routes import Mapper
import os
import cgi
import re

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
    def __init__(self, path, query, session = None):
        self.path = path
        self.query = QueryData(query)
        self.session = session

class Response(object):
    def __init__(self, template, context = {}, statusCode = 200):
        self.template = template
        self.context = context
        self.statusCode = statusCode

class RedirectResponse(object):
    def __init__(self, url):
        self.redirectUrl = QUrl(url)
        self.statusCode = 301

class Session(object):
    def __init__(self):
        self.user = ""
        self.remoteKey = None
    
    def is_auth(self):
        return self.user and True or False
    
    def logout(self):
        self.user = ""
    
    def ff(self):
        import friendfeed
        return friendfeed.FriendFeed(self.user, self.remoteKey)

def filter_likes(entry, user):
    for like in entry["likes"]:
        if like["user"]["nickname"] == user:
            return True
    return False

twitterAtRe = re.compile(r"@([A-Za-z0-9_]+)")
def filter_twitterise(value):
    value = twitterAtRe.sub(r'@<a href="http://twitter.com/\1">\1</a>', value)
    return value

class SiteServer(object):
    def __init__(self):
        self.jinja = Environment(loader = FileSystemLoader("data/templates"), autoescape = True)
        self.jinja.filters["likes"] = filter_likes
        self.jinja.filters["twitterise"] = filter_twitterise

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

    def request(self, url):
        path = str(url.path())
        query = str(url.encodedQuery())
        print "Request:", path + (query and ("?" + query) or "")
        r = self.mapper.match(path)
        if not r:
            return (404, "<h1>404 Not Found</h1><p><a href=\"http://www.google.com/\">Try Google</a>.</p>")
        request = Request(path, query, session = self.session) #@UnusedVariable
        controller = r["controller"]
        action = r["action"]
        del r["controller"]
        del r["action"]
        exec("from %s import %s" % (controller, action))
        exec("response = %s(request, **r)" % action)
        if response.statusCode == 301: #@UndefinedVariable
            return self.request(response.redirectUrl) #@UndefinedVariable
        template = self.jinja.get_template(response.template, globals = { #@UndefinedVariable
            "session": request.session,
            "media": "file://" + os.path.join(os.getcwd(), "data/media"),
        })
        return response.statusCode, template.render(response.context) #@UndefinedVariable

