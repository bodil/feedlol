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
import base64, urllib, simplejson, datetime, time
import base64, urllib, simplejson

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
    
    def post(self, message, link = None, comment = None, room = None):
        post_args = { "title": message }
        if link:
            post_args["link"] = link
        if comment:
            post_args["comment"] = comment
        if room:
            post_args["room"] = room
        return self._request("/api/share", feed = True, post_args = post_args)
    
    def deleteEntry(self, entry_id):
        return self._request("/api/entry/delete", post_args = { "entry": entry_id })
    
    def undeleteEntry(self, entry_id):
        return self._request("/api/entry/delete", post_args = { "entry": entry_id, "undelete": 1 })
    
    def hideEntry(self, entry_id):
        return self._request("/api/entry/hide", post_args = { "entry": entry_id })
    
    def unhideEntry(self, entry_id):
        return self._request("/api/entry/hide", post_args = { "entry": entry_id, "unhide": 1 })
    
    def like(self, id):
        return self._request("/api/like", post_args = { "entry": id })

    def unlike(self, id):
        return self._request("/api/like/delete", post_args = { "entry": id })
    
    def comment(self, entry_id, body):
        return self._request("/api/comment", post_args = { "entry": entry_id, "body": body })

    def editComment(self, entry_id, id, body):
        return self._request("/api/comment", post_args = { "entry": entry_id, "comment": id, "body": body })
    
    def deleteComment(self, entry_id, id):
        return self._request("/api/comment/delete", post_args = { "entry": entry_id, "comment": id })

    def undeleteComment(self, entry_id, id):
        return self._request("/api/comment/delete", post_args = { "entry": entry_id, "comment": id, "undelete": 1 })

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
            result = simplejson.loads(str(self.data).decode("utf-8"))
            if self.feed:
                date_properties = frozenset(("updated", "published"))
                for entry in result.get("entries", []):
                    entry["updated"] = self._parse_date(entry["updated"])
                    entry["published"] = self._parse_date(entry["published"])
                    for comment in entry.get("comments", []):
                        comment["date"] = self._parse_date(comment["date"])
                    for like in entry.get("likes", []):
                        like["date"] = self._parse_date(like["date"])
                result["entries"].sort(key = lambda x:x["updated"], reverse = True)
            self.emit(SIGNAL("ready"), result)
        self.emit(SIGNAL("cleanup"), self)

    def _parse_date(self, date_str):
        rfc3339_date = "%Y-%m-%dT%H:%M:%SZ"
        return datetime.datetime(*time.strptime(date_str, rfc3339_date)[:6])
