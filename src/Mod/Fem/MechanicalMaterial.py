#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013 - Juergen Riegel <FreeCAD@juergen-riegel.net>      *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui
    from PySide import QtCore


__title__ = "Machine-Distortion FemSetGeometryObject managment"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

material_shapes = ['all' ,'remaining' ,'referenced']

def makeMechanicalMaterial(name):
    '''makeMaterial(name): makes an Material
    name there fore is a material name or an file name for a FCMat file'''
    obj = FreeCAD.ActiveDocument.addObject("App::MaterialObjectPython", name)
    _MechanicalMaterial(obj)
    _ViewProviderMechanicalMaterial(obj.ViewObject)
    # FreeCAD.ActiveDocument.recompute()
    return obj


class _CommandMechanicalMaterial:
    "the Fem Material command definition"
    def GetResources(self):
        return {'Pixmap': 'Fem_Material',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Fem_Material", "Mechanical material..."),
                'Accel': "M, M",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Fem_Material", "Creates or edit the mechanical material definition.")}

    def Activated(self):
        mat_objs = []
        for i in FemGui.getActiveAnalysis().Member:
            if i.isDerivedFrom("App::MaterialObject"):
                    mat_objs.append(i)

        if len(mat_objs) == 1 and mat_objs[0].MaterialShapes == 'all':
            FreeCADGui.doCommand("Gui.activeDocument().setEdit('" + mat_objs[0].Name + "',0)")
        else:
            FreeCAD.ActiveDocument.openTransaction("Create Material")
            FreeCADGui.addModule("MechanicalMaterial")
            FreeCADGui.doCommand("MechanicalMaterial.makeMechanicalMaterial('MechanicalMaterial')")
            FreeCADGui.doCommand("App.activeDocument()." + FemGui.getActiveAnalysis().Name + ".Member = App.activeDocument()." + FemGui.getActiveAnalysis().Name + ".Member + [App.ActiveDocument.ActiveObject]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name,0)")

    def IsActive(self):
        if FemGui.getActiveAnalysis():
            return True
        else:
            return False


class _MechanicalMaterial:
    "The Material object"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkList","Reference","Material","List of material shapes")
        obj.addProperty("App::PropertyEnumeration","MaterialShapes","Material","Classification of material shapes")
        obj.MaterialShapes = material_shapes
        obj.setEditorMode("MaterialShapes", 2) # hidden
        obj.MaterialShapes = 'referenced'
        obj.Proxy = self
        self.Type = "MechanicalMaterial"
        # obj.Material = StartMat

    def execute(self, obj):
        return


class _ViewProviderMechanicalMaterial:
    "A View Provider for the MechanicalMaterial object"

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return ":/icons/Fem_Material.svg"

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        taskd = _MechanicalMaterialTaskPanel(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _MechanicalMaterialTaskPanel:
    '''The editmode TaskPanel for MechanicalMaterial objects'''
    def __init__(self, obj):
        self.obj = obj

        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Fem/MechanicalMaterial.ui")
        QtCore.QObject.connect(self.form.pushButton_MatWeb, QtCore.SIGNAL("clicked()"), self.goMatWeb)
        QtCore.QObject.connect(self.form.cb_materials, QtCore.SIGNAL("activated(int)"), self.choose_material)
        QtCore.QObject.connect(self.form.input_fd_young_modulus, QtCore.SIGNAL("valueChanged(double)"), self.ym_changed)
        QtCore.QObject.connect(self.form.spinBox_poisson_ratio, QtCore.SIGNAL("valueChanged(double)"), self.pr_changed)
        QtCore.QObject.connect(self.form.cb_material_shapes, QtCore.SIGNAL("currentIndexChanged(int)"), self.set_material_shapes_classification)
        QtCore.QObject.connect(self.form.pushButton_Reference, QtCore.SIGNAL("clicked()"), self.add_reference)
        self.form.list_References.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.list_References.connect(self.form.list_References, QtCore.SIGNAL("customContextMenuRequested(QPoint)" ), self.reference_list_right_clicked)

        self.previous_material = self.obj.Material
        self.previous_reference = self.obj.Reference
        self.previous_materialshapes = self.obj.MaterialShapes
        self.import_materials()
        previous_mat_path = self.get_material_path(self.previous_material)
        if not previous_mat_path:
            print "Previously used material cannot be found in material directories. Using transient material."
            material_name = self.get_material_name(self.previous_material)
            if material_name != 'None':
                self.add_transient_material(self.previous_material)
                index = self.form.cb_materials.findData(material_name)
            else:
                index = self.form.cb_materials.findText(material_name)
            self.choose_material(index)
        else:
            index = self.form.cb_materials.findData(previous_mat_path)
            self.choose_material(index)

        self.mat_shapes_classification = self.obj.MaterialShapes
        self.references = self.obj.Reference

        if self.mat_shapes_classification == 'all':
            # at startup no currentIndexChanged() is called --> manual calls
            self.form.widget_stack.setCurrentIndex(0)
            self.set_material_shapes_classification(0)
        elif self.mat_shapes_classification == 'remaining':
            self.form.cb_material_shapes.setCurrentIndex(1)
        elif self.mat_shapes_classification == 'referenced':
            # fill data into the list_References items
            self.rebuild_list_References()
            self.form.cb_material_shapes.setCurrentIndex(2)


    def accept(self):
        self.obj.Reference = self.references
        self.obj.MaterialShapes = self.mat_shapes_classification
        if  self.check_material_shape_classification():
            FreeCADGui.ActiveDocument.resetEdit()
            return
        self.obj.Reference = self.previous_reference
        self.obj.MaterialShapes = self.previous_materialshapes

    def reject(self):
        self.obj.Material = self.previous_material
        #print "Reverting to material:"
        #self.print_mat_data(self.previous_material)
        FreeCADGui.ActiveDocument.resetEdit()

    def goMatWeb(self):
        import webbrowser
        webbrowser.open("http://matweb.com")

    def ym_changed(self, value):
        import Units
        old_ym = Units.Quantity(self.obj.Material['YoungsModulus'])
        if old_ym != value:
            material = self.obj.Material
            # FreeCAD uses kPa internall for Stress
            material['YoungsModulus'] = unicode(value) + " kPa"
            self.obj.Material = material

    def pr_changed(self, value):
        import Units
        old_pr = Units.Quantity(self.obj.Material['PoissonRatio'])
        if old_pr != value:
            material = self.obj.Material
            material['PoissonRatio'] = unicode(value)
            self.obj.Material = material

    def choose_material(self, index):
        if index < 0:
            return
        mat_file_path = self.form.cb_materials.itemData(index)
        self.obj.Material = self.materials[mat_file_path]
        self.form.cb_materials.setCurrentIndex(index)
        self.set_mat_params_in_combo_box(self.obj.Material)
        gen_mat_desc = ""
        if 'Description' in self.obj.Material:
            gen_mat_desc = self.obj.Material['Description']
        self.form.l_mat_description.setText(gen_mat_desc)
        #self.print_mat_data(self.obj.Material)

    def get_material_name(self, material):
        if 'Name' in self.previous_material:
            return self.previous_material['Name']
        else:
            return 'None'

    def get_material_path(self, material):
        for a_mat in self.materials:
            unmatched_items = set(self.materials[a_mat].items()) ^ set(material.items())
            if len(unmatched_items) == 0:
                return a_mat
        return ""

    def print_mat_data(self, matmap):
        print 'Material data:'
        print ' Name = {}'.format(self.get_material_name(matmap))
        if 'YoungsModulus' in matmap:
            print ' YM = ', matmap['YoungsModulus']
        if 'PoissonRatio' in matmap:
            print ' PR = ', matmap['PoissonRatio']

    def set_mat_params_in_combo_box(self, matmap):
        if 'YoungsModulus' in matmap:
            ym_new_unit = "MPa"
            ym = FreeCAD.Units.Quantity(matmap['YoungsModulus'])
            ym_with_new_unit = ym.getValueAs(ym_new_unit)
            self.form.input_fd_young_modulus.setText("{} {}".format(ym_with_new_unit, ym_new_unit))
        if 'PoissonRatio' in matmap:
            self.form.spinBox_poisson_ratio.setValue(float(matmap['PoissonRatio']))

    def add_transient_material(self, material):
        material_name = self.get_material_name(material)
        self.form.cb_materials.addItem(QtGui.QIcon(":/icons/help-browser.svg"), material_name, material_name)
        self.materials[material_name] = material

    def add_mat_dir(self, mat_dir, icon):
        import glob
        import os
        import Material
        mat_file_extension = ".FCMat"
        ext_len = len(mat_file_extension)
        dir_path_list = glob.glob(mat_dir + '/*' + mat_file_extension)
        self.pathList = self.pathList + dir_path_list
        material_name_list = []
        for a_path in dir_path_list:
            material_name = os.path.basename(a_path[:-ext_len])
            self.materials[a_path] = Material.importFCMat(a_path)
            material_name_list.append([material_name, a_path])
        material_name_list.sort()
        for mat in material_name_list:
            self.form.cb_materials.addItem(QtGui.QIcon(icon), mat[0], mat[1])

    def import_materials(self):
        self.materials = {}
        self.pathList = []
        self.form.cb_materials.clear()
        self.fem_preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem")
        use_built_in_materials = self.fem_preferences.GetBool("UseBuiltInMaterials", True)
        if use_built_in_materials:
            system_mat_dir = FreeCAD.getResourceDir() + "/Mod/Material/StandardMaterial"
            self.add_mat_dir(system_mat_dir, ":/icons/freecad.svg")

        use_mat_from_config_dir = self.fem_preferences.GetBool("UseMaterialsFromConfigDir", True)
        if use_mat_from_config_dir:
            user_mat_dirname = FreeCAD.getUserAppDataDir() + "Materials"
            self.add_mat_dir(user_mat_dirname, ":/icons/preferences-general.svg")

        use_mat_from_custom_dir = self.fem_preferences.GetBool("UseMaterialsFromCustomDir", True)
        if use_mat_from_custom_dir:
            custom_mat_dir = self.fem_preferences.GetString("CustomMaterialsDir", "")
            self.add_mat_dir(custom_mat_dir, ":/icons/user.svg")

    def set_material_shapes_classification(self,index):
        if index == 0:
            self.form.l_all.setText('all shapes of the model use this material')
            self.mat_shapes_classification = 'all'
            self.references = []
        elif index == 1:
            self.form.l_remaining.setText('all not referenced shapes of the model use this material')
            self.mat_shapes_classification = 'remaining'
            self.references = []
        elif index == 2:
            self.mat_shapes_classification = 'referenced'

    def reference_list_right_clicked(self, QPos):
        self.form.contextMenu = QtGui.QMenu()
        menu_item = self.form.contextMenu.addAction("Remove Reference")
        if len(self.references) == 0:
            menu_item.setDisabled(True)
        self.form.connect(menu_item, QtCore.SIGNAL("triggered()"), self.remove_reference)
        parentPosition = self.form.list_References.mapToGlobal(QtCore.QPoint(0, 0))
        self.form.contextMenu.move(parentPosition + QPos)
        self.form.contextMenu.show()

    def remove_reference(self):
        if len(self.references) == 0: 
            print 'return from remove_reference'
            return
        currentItemName = str(self.form.list_References.currentItem().text())
        for ref in self.references:
            if ref.Name == currentItemName:
                self.references.remove(ref)
        self.rebuild_list_References()

    def add_reference(self):
        '''
        # aktuell solid markieren und button druecken 
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) == 1:
            sel = selection[0]
        else:
            print 'Select one Solid and click on the add Referenc Button to add the shape!'   # selecting more solids --> observer
            return
        if hasattr(sel,"Shape"):
            if sel.Shape.ShapeType == 'Solid':     # TODO faces for shell elements
                #print 'Found a solid: ', sel.Name
                if sel not in self.references:
                    self.references.append(sel)
                    self.rebuild_list_References()
                else:
                    print sel.Name, ' is allready in reference list!'
        else:
            print 'No shape found!'
            return
        '''
        # observer starten, dieser erwartet eingabe
        print 'try to start the observer'
        ReferenceShapeSelectionObserver() # erzeugt instanz meiner observerklasse
        return


    def rebuild_list_References(self):
        self.form.list_References.clear()
        items = []
        for i in self.references:
            items.append(i.Name)
        for listItemName in sorted(items):
            listItem = QtGui.QListWidgetItem(listItemName, self.form.list_References)

    def check_material_shape_classification(self):
        analysis_members = self.obj.InList[0].Member
        materials = []
        for am in analysis_members:
            if am.isDerivedFrom("App::MaterialObjectPython"):
                materials.append(am)
        remaining_material = False
        for m in materials:
            if m.MaterialShapes == 'all' and len(materials) > 1:
                QtGui.QMessageBox.critical(None, "Wrong materials", "If MaterialShapes of a material is set to 'all' only one material should be used")
                return False
            elif m.MaterialShapes == 'remaining' and remaining_material == False:
                remaining_material = True
                continue # jump to next m in materials
            elif m.MaterialShapes == 'remaining' and remaining_material == True:
                QtGui.QMessageBox.critical(None, "Wrong materials", "MaterialShapes is set to 'remaining' for mor than one material")
                return False
            elif m.MaterialShapes == 'referenced' and len(m.Reference) == 0:
                QtGui.QMessageBox.critical(None, "Wrong materials", "At least one material has an empty reference list")
                return False
        return True



class ReferenceShapeSelectionObserver:
    """ReferenceShapeSelectionObserver
       started bei click auf button addrefference, da dort instanz dieses observers erzeugt wird"""
    def __init__(self):
        print 'konstruktor des observers'
        self.selected_ref_shape = None
        FreeCADGui.Selection.addObserver(self)
        FreeCAD.Console.PrintMessage("Select an Solid\n")
    
    def addSelection(self, doc, obj, sub, pos):
        sel = FreeCAD.getDocument(doc).getObject(obj)
        if hasattr(sel,"Shape"):
            if sel.Shape.ShapeType == 'Solid':     # TODO faces for shell elements
                print 'The observer found a solid: ', sel, ' --> ', type(sel)
                # we have our selection --> remove the observer
                FreeCADGui.Selection.removeObserver(self)
                self.selected_ref_shape = sel

                #if sel not in self.references:
                #    self.references.append(sel)
                #    self.rebuild_list_References()
                #else:
                #    print sel.Name, ' is allready in reference list!'
        else:
            print 'No shape found!'

        #return self.selected_ref_shape  # mhh aber habe eine instanz erzeugt, kann die was zurueckgeben
        
        # aktuell remove ich den observer und er wird nur auf klick auf addReference weider gestarted :-(
        # das will ich ja grade nicht ich will solid fuer solik anklicken und der observer soll erst 
        # bei klick auf andere funktion removed werden, aber wenigstens wird der solid nach dem klick auf button genommen. 




FreeCADGui.addCommand('Fem_MechanicalMaterial', _CommandMechanicalMaterial())
