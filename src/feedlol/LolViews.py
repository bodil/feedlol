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

from SiteServer import Response, RedirectResponse, DeferredResponse
from urllib2 import HTTPError, URLError

def feed(request, user = None):
    if not request.session.is_auth():
        return RedirectResponse("chrome:/login")
    if user == "me":
        user = request.session.user
    if user:
        return DeferredResponse(request.ff.userFeed(user), feedReady, feedError)
    else:
        return DeferredResponse(request.ff.homeFeed(), feedReady, feedError)

def feedReady(request, data, user = None):
    feed = data
    print feed["entries"][0]
    entries = []
    last = None
    for i in feed["entries"]:
        if last and last["user"]["id"] == i["user"]["id"] and last["service"]["id"] == i["service"]["id"]:
            entry.append(i)
        else:
            entry = [i]
            entries.append(entry)
            last = i
    title = user and feed["entries"][0]["user"]["name"] or "Friends"
    return Response("feed.html", { "feed": entries, "title": title })

def feedError(request, error, user = None):
    request.session.logout()
    return RedirectResponse("chrome:/login")

def login(request):
    try:
        username = request.query.username
        remotekey = request.query.remotekey
    except AttributeError:
        return Response("login.html")
    request.session.user = username
    request.session.remoteKey = remotekey
    return RedirectResponse("chrome:/")

