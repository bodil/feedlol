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

from PyQt4.QtCore import Qt, QSize, QRect, QPoint, QTimer, SIGNAL, QUrl, QRectF
from PyQt4.QtGui import QWidget, QCursor, QPixmap, QPainter, QApplication, QFont, \
    QFontMetrics, QTextOption, QPen
from PyQt4.QtWebKit import QWebView

class PreviewTooltip(QWidget):
    def __init__(self, url):
        QWidget.__init__(self, None, Qt.ToolTip)
        self.url = url
        
        self.font = QFont(QApplication.font(self))
        self.font.setPointSize(8)
        
        desktop = QApplication.desktop().availableGeometry(self)
        cursor = QCursor.pos()
        rect = QRect(cursor + QPoint(-10, 10), QSize(240,180 + QFontMetrics(self.font).height()))
        if rect.left() < desktop.left():
            rect.moveLeft(desktop.left())
        if rect.right() > desktop.right():
            rect.moveRight(cursor.x() - 10)
        if rect.bottom() > desktop.bottom():
            rect.moveBottom(cursor.y() - 10)
        self.setGeometry(rect)
        
        self.pixmap = None
        self.progress = 0
        self.title = unicode(self.url)

        self.webView = QWebView()
        self.webView.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.webView.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.webView.resize(1024,768)
        self.webView.load(QUrl(url))
        
        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"), self.refresh)
        self.timer.start(3000)
        
        self.connect(self.webView, SIGNAL("loadFinished(bool)"), self.refresh)
        self.connect(self.webView, SIGNAL("loadProgress(int)"), self.updateProgress)
        self.connect(self.webView, SIGNAL("urlChanged(const QUrl&)"), self.newUrl)
        self.connect(self.webView, SIGNAL("titleChanged(const QString&)"), self.newTitle)

    def updateProgress(self, progress):
        self.progress = progress
        self.update()
    
    def newUrl(self, url):
        self.title = unicode(url.toString())
        self.update()
    
    def newTitle(self, title):
        self.title = unicode(title)
        self.update()

    def refresh(self):
        view = QPixmap(self.webView.size())
        self.webView.render(view)
        self.pixmap = view.scaled(QSize(240,180), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.update()
    
    def paintEvent(self, event):
        QWidget.paintEvent(self, event)
        p = QPainter(self)
        p.setFont(self.font)
        if self.pixmap:
            p.drawPixmap(QPoint(0,0), self.pixmap)
        r = QRect(self.rect().topLeft() + QPoint(0, 180), QSize(self.rect().size().width(), p.fontMetrics().height()))
        p.fillRect(r, self.palette().midlight())
        if self.progress:
            pr = QRect(r)
            pr.setWidth( (r.width() * self.progress) / 100 )
            p.fillRect(pr, self.palette().dark())
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(self.palette().text(), 1))
        p.drawText(QRectF(r), self.title, QTextOption(Qt.AlignHCenter))
        p.setPen(QPen(self.palette().shadow(), 1))
        p.drawRect(self.rect().adjusted(0,0,-1,-1))
