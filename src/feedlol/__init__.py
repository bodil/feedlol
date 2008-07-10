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

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import SIGNAL, SLOT, QResource
from FeedLol import FeedLol

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setOrganizationName("bodil.tv")
    app.setOrganizationDomain("bodil.tv")
    app.setApplicationName("FeedLol")
    app.setApplicationVersion("0.1")
    lol = FeedLol()
    lol.show()
    rv = app.exec_()
    lol.saveState()
    sys.exit(rv)
