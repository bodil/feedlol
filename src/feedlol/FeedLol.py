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

from PyQt4.QtCore import SIGNAL, SLOT, QSettings, QVariant
from PyQt4.QtGui import QMainWindow, QAction, QIcon, QProgressBar, QToolBar, \
    QKeySequence, QDialog
from PyQt4.QtNetwork import QNetworkProxy
from SettingsDialog import SettingsDialog
from feedlol.FeedView import FeedView

class FeedLol(QMainWindow):
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle("FeedLol")
        
        self.aboutAction = QAction(QIcon("data/icons/help-about.svg"), "&About FeedLol...", self)
        self.connect(self.aboutAction, SIGNAL("triggered()"), self.slotAbout)
        
        self.reloadAction = QAction(QIcon("data/icons/view-refresh.svg"), "&Reload", self)
        self.reloadAction.setShortcut(QKeySequence.Refresh)
        
        self.homeAction = QAction(QIcon("data/icons/go-home.svg"), "Go &Home", self)
        self.homeAction.setShortcut("Alt+Home")
        
        self.userAction = QAction(QIcon("data/icons/user-identity.svg"), "&Me", self)
        self.userAction.setShortcut("Ctrl+M")
        
        self.logoutAction = QAction(QIcon("data/icons/dialog-close.svg"), "Log&out", self)
        self.logoutAction.setShortcut(QKeySequence.Close)
        
        self.settingsAction = QAction(QIcon("data/icons/configure.svg"), "&Preferences...", self)
        self.connect(self.settingsAction, SIGNAL("triggered()"), self.slotSettings)

        self.toolbar = QToolBar(self)
        self.toolbar.addAction(self.homeAction)
        self.toolbar.addAction(self.userAction)
        self.toolbar.addAction(self.reloadAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.logoutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settingsAction)
        self.toolbar.addAction(self.aboutAction)
        self.addToolBar(self.toolbar)
        
        self.loadStatus = QProgressBar(self)
        self.loadStatus.setRange(0, 100)
        self.loadStatus.setMaximumWidth(200)
        self.loadStatus.setTextVisible(False)
        self.loadStatus.hide()
        self.statusBar().addPermanentWidget(self.loadStatus)

        self.feedView = FeedView(self)
        self.setCentralWidget(self.feedView)
        self.connect(self.feedView, SIGNAL("titleChanged(const QString&)"), self.slotSetTitle)
        self.connect(self.feedView, SIGNAL("statusBarMessage(const QString&)"), self.statusBar(), SLOT("showMessage(const QString&)"))
        self.connect(self.feedView, SIGNAL("loadStarted()"), self.loadStart)
        self.connect(self.feedView, SIGNAL("loadFinished(bool)"), self.loadStop)
        self.connect(self.feedView, SIGNAL("loadProgress(int)"), self.loadProgress)
        self.connect(self.feedView.page(), SIGNAL("linkHovered(const QString&, const QString&, const QString&)"), self.linkHovered)
        self.connect(self.reloadAction, SIGNAL("triggered()"), self.feedView.reload)
        self.connect(self.homeAction, SIGNAL("triggered()"), self.feedView.goHome)
        self.connect(self.userAction, SIGNAL("triggered()"), self.feedView.goToUserPage)
        self.connect(self.logoutAction, SIGNAL("triggered()"), self.feedView.logout)
        
        self.settingsDialog = SettingsDialog(self.feedView, self)

        settings = QSettings()
        
        if settings.contains("proxy/type"):
            proxy = QNetworkProxy()
            proxyType = settings.value("proxy/type").toInt()[0]
            proxy.setType( (proxyType == 2) and QNetworkProxy.Socks5Proxy or ( (proxyType == 1) and QNetworkProxy.HttpProxy or QNetworkProxy.NoProxy ) )
            if proxy.type() != QNetworkProxy.NoProxy:
                proxy.setHostName(settings.value("proxy/host").toString())
                proxy.setPort(settings.value("proxy/port").toInt()[0])
                if settings.value("proxy/user").toString():
                    proxy.setUser(settings.value("proxy/user").toString())
                    proxy.setPassword(settings.value("proxy/password").toString())
            QNetworkProxy.setApplicationProxy(proxy)

        if settings.contains("mainWindow/geometry"):
            self.restoreGeometry(settings.value("mainWindow/geometry").toByteArray())
        else:
            self.resize(320,480)

        self.feedView.goHome()
        
    def saveState(self):
        settings = QSettings()
        settings.setValue("mainWindow/geometry", QVariant(self.saveGeometry()))
        session = self.feedView.siteServer.session
        from cPickle import dumps
        session = dumps(session)
        settings.setValue("session", QVariant(session))
        proxy = QNetworkProxy.applicationProxy()
        proxyType = (proxy.type() == QNetworkProxy.Socks5Proxy) and 2 or ( (proxy.type() == QNetworkProxy.HttpProxy) and 1 or 0 )
        settings.setValue("proxy/type", QVariant(proxyType))
        settings.setValue("proxy/host", QVariant(proxy.hostName()))
        settings.setValue("proxy/port", QVariant(proxy.port()))
        settings.setValue("proxy/user", QVariant(proxy.user()))
        settings.setValue("proxy/password", QVariant(proxy.password()))

    def slotAbout(self):
        from PyQt4.QtGui import QMessageBox
        QMessageBox.about(self, "FeedLol", "<h2>FeedLol 0.1</h2><p>Copyright &copy; 2008 <a href=\"mailto:bodil@bodil.tv\">Bodil Stokke</a></p>")
        
    def slotSettings(self):
        self.settingsDialog.updateSettings()
        if self.settingsDialog.exec_() == QDialog.Accepted:
            self.settingsDialog.applySettings()

    def slotSetTitle(self, title):
        self.setWindowTitle("FeedLol: " + title)
        
    def loadStart(self):
        self.loadStatus.show()
    
    def loadStop(self):
        self.loadStatus.hide()
        
    def loadProgress(self, progress):
        self.loadStatus.setValue(progress)
    
    def linkHovered(self, url, title, text):
        if url:
            self.statusBar().showMessage(url)
        else:
            self.statusBar().clearMessage()
