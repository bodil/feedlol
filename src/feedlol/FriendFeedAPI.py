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

from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from PyQt4.QtCore import SIGNAL, QObject, QUrl, QByteArray
import base64, urllib, cjson

class FriendFeedAPI(QObject):
    def __init__(self, session = None, url = "http://friendfeed.com/", manager = QNetworkAccessManager(), parent = None):
        QObject.__init__(self, parent)
        self.manager = manager
        self.session = session
        self.url = QUrl(url)
        self.activeRequests = set()

    def homeFeed(self):
        return self._request("/api/feed/home", feed = True)
    
    def userFeed(self, nickname):
        return self._request("/api/feed/user/" + urllib.quote_plus(nickname), feed = True)

    def _request(self, path, feed = False, post_args = None, **url_args):
        url = self.url.resolved(QUrl(path))
        for key in url_args:
            url.addQueryItem(key, url_args[key])
        url.addQueryItem("format", "json")
        print "ff req:", url
        req = QNetworkRequest(url)
        if self.session and self.session.is_auth():
            req.setRawHeader("Authorization", "Basic " + base64.b64encode("%s:%s" % (self.session.user, self.session.remoteKey)))
        if post_args:
            data = urllib.urlencode(post_args)
            reply = self.manager.post(req, data)
        else:
            reply = self.manager.get(req)
        req = FriendFeedRequest(reply, feed)
        self.activeRequests.add(req)
        self.connect(req, SIGNAL("cleanup"), self._cleanup)
        return req
    
    def _cleanup(self, req):
        self.activeRequests.remove(req)

class FriendFeedRequest(QObject):
    def __init__(self, reply, feed = False, parent = None):
        QObject.__init__(self, parent)
        self.reply = reply
        self.feed = feed
        self.connect(self.reply, SIGNAL("readyRead()"), self.readData)
        self.connect(self.reply, SIGNAL("finished()"), self.dataDone)
        self.data = QByteArray()

    def readData(self):
        self.data.append(self.reply.readAll())
    
    def dataDone(self):
        if self.reply.error() != QNetworkReply.NoError:
            self.emit(SIGNAL("error"), self.reply.error())
        else:
            self.data.append(self.reply.readAll())
            self.emit(SIGNAL("ready"), cjson.decode(str(self.data).decode("utf-8")))
        self.emit(SIGNAL("cleanup"), self)
