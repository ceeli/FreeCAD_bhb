import unittest

from PySide import QtCore
from PySide import QtGui
from PySide.QtTest import QTest

import FreeCAD
import FreeCADGui
import FCTest


class TaskPanelTest(FCTest.DocumentTest):
    """ Unittest test case base for testing task panels. """

    def tearDown(self):
        FreeCADGui.Control.closeDialog()
        super().tearDown()

    def getTaskPanel(self, name):
        """ Return the QWidget of the currently open task panel.

        This method searches for a QWidget with the ``objectName`` *name* only
        inside the combo view. This is not the python task panel object but the
        QWidget that is used by it (set as self.form of the task panel object).

        :param name: The ``objectName`` of the QWidget of the task panel.

        :returns:
            QWidget of the currently open task panel or ``None`` if no task
            panel is open.
        """
        mw = FreeCADGui.getMainWindow()
        cv = mw.findChild(QtGui.QWidget, "Combo View")
        return cv.findChild(QtGui.QWidget, name)

    def clickButton(self, button):
        """ Click a button above the open task panel.

        Simulate a click in the center of the buttons that are above task panel
        (e.g. Apply and Cancel). Which button to press is specified by the
        *button* argument. This event is simulated internally using QTest so
        the mouse won't move when calling this function.

        :param button:
            Must be one of Qt's dialog standard buttons. The most prominent
            ones used by task panels are:
            
             - ``QtGui.QDialogButtonBox.Ok``
             - ``QtGui.QDialogButtonBox.Apply``
             - ``QtGui.QDialogButtonBox.Cancel``
             - ``QtGui.QDialogButtonBox.Close``
        """
        bp = self._getButtonParent()
        btt = bp.button(button)
        if btt is not None:
            QTest.mouseClick(btt, QtCore.Qt.MouseButton.LeftButton)

    def _getButtonParent(self):
        mw = FreeCADGui.getMainWindow()
        cv = mw.findChild(QtGui.QWidget, "Combo View")
        ct = cv.findChild(QtGui.QWidget, "combiTab")
        sw = ct.findChild(QtGui.QStackedWidget)
        sa = sw.findChild(QtGui.QScrollArea)
        qf = sa.findChild(QtGui.QFrame)
        bb = qf.findChild(QtGui.QDialogButtonBox)
        return bb
