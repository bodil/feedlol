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

from PyQt4.QtCore import QObject, pyqtSignature, QUrl

class JavascriptAPI(QObject):
    def __init__(self, site, parent = None):
        QObject.__init__(self, parent)
        self.site = site
    
    @pyqtSignature("const QString&")
    def log(self, text):
        print text

    @pyqtSignature("const QString&")
    def like(self, id):
        self.site.ff.like(id)

    @pyqtSignature("const QString&")
    def unlike(self, id):
        self.site.ff.unlike(id)

    @pyqtSignature("const QString&")
    def notify(self, url):
        statusCode, html = self.site.request(QUrl(url))
        if statusCode == 200:
            self.site.notes.notify(html)
        return statusCode

    @pyqtSignature("")
    def getOpenFile(self):
        from PyQt4.QtGui import QFileDialog
        return QFileDialog.getOpenFileName()

    @pyqtSignature("")
    def getOpenFiles(self):
        from PyQt4.QtGui import QFileDialog
        return QFileDialog.getOpenFileNames()

