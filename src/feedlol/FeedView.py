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

from JavascriptAPI import JavascriptAPI
from PyQt4.QtCore import SIGNAL, QUrl
from PyQt4.QtGui import QDesktopServices, QPixmap
from PyQt4.QtWebKit import QWebView, QWebPage, QWebSettings
from SiteServer import SiteServer
from feedlol.PreviewTooltip import PreviewTooltip
import os

class FeedView(QWebView):
    def __init__(self, parent = None):
        QWebView.__init__(self, parent)
        self.setMinimumSize(320, 480)
        self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        self.page().setForwardUnsupportedContent(True)
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        QWebSettings.setWebGraphic(QWebSettings.MissingImageGraphic, QPixmap("data/media/missing.png"))
        self.siteServer = SiteServer()
        self.previewTooltip = None
        self.connect(self.page(), SIGNAL("linkClicked(const QUrl&)"), self.slotLinkClicked)
        self.connect(self.page(), SIGNAL("unsupportedContent(QNetworkReply*)"), self.slotHandleReply)
        self.connect(self.page(), SIGNAL("frameCreated(QWebFrame*)"), self.setupFrame)
        # NOTE: This simplified mechanism depends on the application NEVER using framesets!
        self.connect(self.page().mainFrame(), SIGNAL("javaScriptWindowObjectCleared()"), self.setupFrame)
        self.connect(self.page(), SIGNAL("linkHovered(const QString&, const QString&, const QString&)"), self.linkHovered)
        
    def goHome(self):
        self.load(QUrl("chrome:/"))
    
    def goToUserPage(self):
        self.load(QUrl("chrome:/user/me"))
        
    def logout(self):
        self.siteServer.session.logout()
        self.goHome()

    def slotLinkClicked(self, url):
        print "clicked:", url
        if url.scheme() == "chrome":
            self.loadPage(url)
        else:
            QDesktopServices.openUrl(url)
    
    def slotHandleReply(self, reply):
        print "unhandled:", reply.url()
        if reply.url().scheme() == "chrome":
            self.loadPage(reply.url())
        return
    
    def setupFrame(self, frame = None):
        if not frame:
            frame = self.page().mainFrame()
        frame.addToJavaScriptWindowObject("feedlol", JavascriptAPI(self.siteServer))

    def loadPage(self, url):
        statusCode, content = self.siteServer.request(url)
        self.setHtml(content, url)

    def linkHovered(self, url, title, text):
        if url and QUrl(url).scheme() != "chrome":
            if self.previewTooltip and self.previewTooltip.url == url:
                return
            self.previewTooltip = PreviewTooltip(url)
            self.previewTooltip.show()
        else:
            if self.previewTooltip:
                self.previewTooltip.deleteLater()
            self.previewTooltip = None

    def leaveEvent(self, event):
        self.linkHovered(None, None, None)

    def focusOutEvent(self, event):
        self.linkHovered(None, None, None)

