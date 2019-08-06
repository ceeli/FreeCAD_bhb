from PySide import QtCore
from PySide import QtGui

import FreeCAD
import FreeCADGui
import GuiTest
import ObjectsFem


class TestGmshTaskPanel(GuiTest.TaskPanelTest):

    def openTaskPanel(self, mesh):
        vDoc = mesh.ViewObject.Document
        vDoc.setEdit(mesh.Name)

    def closeTaskPanel(self, mesh):
        vDoc = mesh.ViewObject.Document
        vDoc.resetEdit()

    def testCubeDefaultMesh(self):
        cube = self.doc.addObject("Part::Box")
        self.doc.recompute()
        mesh = ObjectsFem.makeMeshGmsh(self.doc, "FEMMeshGmsh")
        mesh.Part = cube
        self.openTaskPanel(mesh)
        self.assertEqual(mesh.FemMesh.NodeCount, 0)
        self.clickButton(QtGui.QDialogButtonBox.Apply)
        self.clickButton(QtGui.QDialogButtonBox.Ok)
        self.assertNotEqual(mesh.FemMesh.NodeCount, 0)

    def testCubeNoMesh(self):
        cube = self.doc.addObject("Part::Box")
        self.doc.recompute()
        mesh = ObjectsFem.makeMeshGmsh(self.doc, "FEMMeshGmsh")
        mesh.Part = cube
        self.openTaskPanel(mesh)
        self.assertEqual(mesh.FemMesh.NodeCount, 0)
        self.clickButton(QtGui.QDialogButtonBox.Ok)
        self.assertEqual(mesh.FemMesh.NodeCount, 0)
