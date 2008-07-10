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

from PyQt4 import uic
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QDialog, QIcon
from PyQt4.QtNetwork import QNetworkProxy

class SettingsDialog(QDialog):
    def __init__(self, feedView, parent = None):
        QDialog.__init__(self, parent)
        self.feedView = feedView
        uic.loadUi("data/settings.ui", self)
        
        # Fix icons
        self.okButton.setIcon(QIcon("data/icons/dialog-ok.svg"))
        self.cancelButton.setIcon(QIcon("data/icons/dialog-cancel.svg"))
        self.pageSelector.item(0).setIcon(QIcon("data/icons/user-identity.svg"))
        self.pageSelector.item(1).setIcon(QIcon("data/icons/preferences-system-network.svg"))
        
        self.connect(self.proxyType, SIGNAL("currentIndexChanged(int)"), self.updateState)
        self.connect(self.proxyAuth, SIGNAL("stateChanged(int)"), self.updateState)
        
        self.pageSelector.setCurrentItem(self.pageSelector.item(0))
        
        self.updateSettings()

    def updateSettings(self):
        self.ffNickname.clear()
        self.ffRemoteKey.clear()
        if self.feedView.siteServer.session.user:
            self.ffNickname.setText(self.feedView.siteServer.session.user)
        if self.feedView.siteServer.session.remoteKey:
            self.ffRemoteKey.setText(self.feedView.siteServer.session.remoteKey)
                
        proxy = QNetworkProxy.applicationProxy()
        self.proxyType.setCurrentIndex( (proxy.type() == QNetworkProxy.Socks5Proxy) and 2 or ( (proxy.type() == QNetworkProxy.HttpProxy) and 1 or 0 ) )
        if self.proxyType.currentIndex() != 0:
            self.proxyHost.setText(proxy.hostName())
            self.proxyPort.setValue(proxy.port())
            if proxy.user():
                self.proxyAuth.setCheckState(Qt.Checked)
                self.proxyAuthUser.setText(proxy.user())
                self.proxyAuthPassword.setText(proxy.password())
    
    def applySettings(self):
        if self.feedView.siteServer.session.user != str(self.ffNickname.text()) or self.feedView.siteServer.session.remoteKey != str(self.ffRemoteKey.text()):
            self.feedView.siteServer.session.user = str(self.ffNickname.text())
            self.feedView.siteServer.session.remoteKey = str(self.ffRemoteKey.text())
            self.feedView.goHome()

        proxy = QNetworkProxy()
        proxyType = self.proxyType.currentIndex()
        proxy.setType( (proxyType == 2) and QNetworkProxy.Socks5Proxy or ( (proxyType == 1) and QNetworkProxy.HttpProxy or QNetworkProxy.NoProxy ) )
        if proxyType:
            proxy.setHostName(self.proxyHost.text())
            proxy.setPort(self.proxyPort.value())
            if self.proxyAuth.checkState() == Qt.Checked:
                proxy.setUser(self.proxyAuthUser.text())
                proxy.setPassword(self.proxyAuthPassword.text())
        QNetworkProxy.setApplicationProxy(proxy)

    def updateState(self):
        on = self.proxyType.currentIndex() and True or False
        auth = on and (self.proxyAuth.checkState() == Qt.Checked) or False
        
        self.proxyHostLabel.setEnabled(on)
        self.proxyHost.setEnabled(on)
        self.proxyPortLabel.setEnabled(on)
        self.proxyPort.setEnabled(on)
        self.proxyAuth.setEnabled(on)
        self.proxyAuthUserLabel.setEnabled(auth)
        self.proxyAuthUser.setEnabled(auth)
        self.proxyAuthPasswordLabel.setEnabled(auth)
        self.proxyAuthPassword.setEnabled(auth)
