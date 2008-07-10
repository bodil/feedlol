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

from PyQt4.QtWebKit import QWebView
from PyQt4.QtGui import QWidget, QLabel, QApplication
from PyQt4.QtCore import QObject, QTimer, SIGNAL, Qt, QRect, QSize, QPoint

class Notification(QWebView):
    def __init__(self, html, timeout = 6000):
        QWebView.__init__(self)
        self.setWindowFlags(Qt.ToolTip | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setHtml(html)
        self.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.timeout = timeout
        self.resize(300, 100)
    
    def display(self):
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"), self.fadeIn)
        self.timer.start(10)
    
    def fadeIn(self):
        op = self.windowOpacity()
        op += 0.01
        if op >= 1.0:
            op = 1.0
            self.timer.stop()
            QTimer.singleShot(self.timeout, self.startFadeOut)
        self.setWindowOpacity(op)
    
    def startFadeOut(self):
        self.timer = QTimer(self)
        self.timer.setInterval(10)
        self.connect(self.timer, SIGNAL("timeout()"), self.fadeOut)
        self.timer.start()

    def fadeOut(self):
        op = self.windowOpacity()
        op -= 0.01
        if op <= 0.0:
            op = 0.0
            self.timer.stop()
        self.setWindowOpacity(op)
        if op == 0.0:
            self.hide()
            QTimer.singleShot(2000, self.bye)
    
    def bye(self):
        self.emit(SIGNAL("done"), self)
        self.deleteLater()

class NotificationServer(QObject):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        self.notifications = set()
        self.size = QSize(300, 100)
        self.margin = QPoint(10, 10)

    def notify(self, html):
        note = Notification(html)
        self.connect(note, SIGNAL("done"), self.noteDestroyed)

        desktop = QApplication.desktop().availableGeometry(note)
        me = QRect(QPoint(0,0), self.size)
        me.moveBottomRight(desktop.bottomRight() - self.margin)
        while self.notePosTaken(me):
            me.translate(0, 0 - (self.size.height() + (self.margin.y() * 2)))
            if not desktop.contains(me):
                me.moveBottom(desktop.bottom() - self.margin.y())
                me.translate(0 - (self.size.width() + self.margin.x() * 2), 0)

        note.setGeometry(me)        
        self.notifications.add(note)
        note.display()

    def notePosTaken(self, rect):
        for note in self.notifications:
            if note.geometry().intersects(rect):
                return True
        return False

    def noteDestroyed(self, note):
        self.notifications.remove(note)
