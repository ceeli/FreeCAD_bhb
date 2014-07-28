#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2011                                                    *  
#*   Yorik van Havre <yorik@uncreated.net>                                 *  
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

import ifcReader, FreeCAD, Arch, Draft, os, sys, time, Part, DraftVecUtils
from DraftTools import translate

__title__="FreeCAD IFC importer"
__author__ = "Yorik van Havre"
__url__ = "http://www.freecadweb.org"

# config
subtractiveTypes = ["IfcOpeningElement"] # elements that must be subtracted from their parents
SCHEMA = "http://www.steptools.com/support/stdev_docs/ifcbim/ifc4.exp" # only for internal prser
MAKETEMPFILES = False # if True, shapes are passed from ifcopenshell to freecad through temp files
DEBUG = True # this is only for the python console, this value is overridden when importing through the GUI
SKIP = ["IfcBuildingElementProxy","IfcFlowTerminal","IfcFurnishingElement"] # default. overwritten by the GUI options
# end config

# supported ifc products (export only):
supportedIfcTypes = ["IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcBeam", "IfcBeamStandardCase",
                     "IfcChimney", "IfcColumn", "IfcColumnStandardCase", "IfcCovering", "IfcCurtainWall",
                     "IfcDoor", "IfcDoorStandardCase", "IfcMember", "IfcMemberStandardCase", "IfcPlate",
                     "IfcPlateStandardCase", "IfcRailing", "IfcRamp", "IfcRampFlight", "IfcRoof",
                     "IfcSlab", "IfcStair", "IfcStairFlight", "IfcWall","IfcSpace",
                     "IfcWallStandardCase", "IfcWindow", "IfcWindowStandardCase", "IfcBuildingElementProxy",
                     "IfcPile", "IfcFooting", "IfcReinforcingBar", "IfcTendon"]
# TODO : shading device not supported?

if open.__module__ == '__builtin__':
    pyopen = open # because we'll redefine open below

def open(filename,skip=None):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docname)
    doc.Label = decode(docname)
    FreeCAD.ActiveDocument = doc
    getConfig()
    read(filename,skip)
    setView()
    #volumeTest()
    #farbImport()
    return doc

def insert(filename,docname,skip=None):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc
    getConfig()
    read(filename,skip)
    return doc
    
def getConfig():
    "Gets Arch IFC import preferences"
    global SKIP, CREATE_IFC_GROUPS, ASMESH, PREFIX_NUMBERS, FORCE_PYTHON_PARSER, SEPARATE_OPENINGS, SEPARATE_PLACEMENTS, JOINSOLIDS, AGGREGATE_WINDOWS
    IMPORT_IFC_FURNITURE = False
    ASMESH = ["IfcFurnishingElement"]
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
    CREATE_IFC_GROUPS = p.GetBool("createIfcGroups",False)
    FORCE_PYTHON_PARSER = p.GetBool("forceIfcPythonParser",False) 
    DEBUG = p.GetBool("ifcDebug",False)
    SEPARATE_OPENINGS = p.GetBool("ifcSeparateOpenings",False)
    SEPARATE_PLACEMENTS = p.GetBool("ifcSeparatePlacements",False)
    PREFIX_NUMBERS = p.GetBool("ifcPrefixNumbers",False)
    JOINSOLIDS = p.GetBool("ifcJoinSolids",False)
    AGGREGATE_WINDOWS = p.GetBool("ifcAggregateWindows",False)
    skiplist = p.GetString("ifcSkip","")
    if skiplist:
        SKIP = skiplist.split(",")
    asmeshlist = p.GetString("ifcAsMesh","")
    if asmeshlist:
        ASMESH = asmeshlist.split(",")

def getIfcOpenShell():
    "locates and imports ifcopenshell"
    global IFCOPENSHELL5
    global IfcImport
    IFCOPENSHELL5 = False
    try:
        import IfcImport
    except:
        try:
            import ifc_wrapper as IfcImport
        except:
            FreeCAD.Console.PrintMessage(translate("Arch","Couldn't locate IfcOpenShell\n"))
            return False
        else:
            IFCOPENSHELL5 = True
            return True
    else:
        if hasattr(IfcImport,"IfcFile"):
            IFCOPENSHELL5 = True
        return True

def read(filename,skip=None):
    "Parses an IFC file"

    # parsing the IFC file
    t1 = time.time()
    
    processedIds = []
    skipIds = skip
    if not skipIds:
        skipIds = []
    elif isinstance(skipIds,int):
        skipIds = [skipIds]
    
    if getIfcOpenShell() and not FORCE_PYTHON_PARSER:
        # use the IfcOpenShell parser
        
        # preparing IfcOpenShell
        if DEBUG: global ifcObjects,ifcParents
        ifcObjects = {} # a table to relate ifc id with freecad object
        ifcParents = {} # a table to relate ifc id with parent id
        if SEPARATE_OPENINGS: 
            if not IFCOPENSHELL5:
                if hasattr(IfcImport,"DISABLE_OPENING_SUBTRACTIONS"):
                    IfcImport.Settings(IfcImport.DISABLE_OPENING_SUBTRACTIONS,True)
        else:
            SKIP.append("IfcOpeningElement")
        useShapes = False
        if IFCOPENSHELL5:
            useShapes = True
            if hasattr(IfcImport,"clean"):
                IfcImport.clean()
        elif hasattr(IfcImport,"USE_BREP_DATA"):
            IfcImport.Settings(IfcImport.USE_BREP_DATA,True)
            useShapes = True
        else:
            if DEBUG: print "Warning: IfcOpenShell version very old, unable to handle Brep data"

        # opening file
        if IFCOPENSHELL5:
            global ifc
            ifc = IfcImport.open(filename)
            objects = ifc.by_type("IfcProduct")
            num_lines = len(objects)
            relations = ifc.by_type("IfcRelAggregates") + ifc.by_type("IfcRelContainedInSpatialStructure") + ifc.by_type("IfcRelVoidsElement")
            propertyrelations = ifc.by_type("IfcRelDefinesByProperties")
            materialrelations = ifc.by_type("IfcRelAssociatesMaterial")
            if not objects:
                print "Error opening IFC file"
                return 
        else:
            num_lines = sum(1 for line in pyopen(filename))
            if not IfcImport.Init(filename):
                print "Error opening IFC file"
                return
                
        # processing geometry
        if DEBUG: print (" ")
        if DEBUG: print ("------------------ processing geometry--------------------")
        idx = 0
        while True:
            objparentid = []
            if IFCOPENSHELL5:
                #if DEBUG: print (" ")
                if DEBUG: print (" ")
                if DEBUG: print ("------------------Object " + str(idx) + " --------------------")
                obj = objects[idx]
                idx += 1
                objid = int(str(obj).split("=")[0].strip("#"))
                objname = obj.get_argument(obj.get_argument_index("Name"))
                objtype = str(obj).split("=")[1].split("(")[0]
                for r in relations:
                    if r.is_a("IfcRelAggregates"):
                        for c in getAttr(r,"RelatedObjects"):
                            if str(obj) == str(c):
                                objparentid.append(int(str(getAttr(r,"RelatingObject")).split("=")[0].strip("#")))
                    elif r.is_a("IfcRelContainedInSpatialStructure"):
                        for c in getAttr(r,"RelatedElements"):
                            if str(obj) == str(c):
                                objparentid.append(int(str(getAttr(r,"RelatingStructure")).split("=")[0].strip("#")))
                    elif r.is_a("IfcRelVoidsElement"):
                        if str(obj) == str(getAttr(r,"RelatedOpeningElement")):
                            objparentid.append(int(str(getAttr(r,"RelatingBuildingElement")).split("=")[0].strip("#")))
 
                
                # get attributes from the object
                objectAttributes = getObjectAttributes(objid, objtype, objname)     # Attributes
                objectPropertySets = getObjectPropertySets(obj, propertyrelations)  # PropertySets
                objectMaterials = getObjectMaterials(obj, materialrelations)        # Materials

 
            else:
                if hasattr(IfcImport, 'GetBrepData'):
                    obj = IfcImport.GetBrepData()  
                else: 
                    obj = IfcImport.Get()
                objid = obj.id
                idx = objid
                objname = obj.name
                objtype = obj.type
                objparentid.append(obj.parent_id)
            if DEBUG: print "["+str(int((float(idx)/num_lines)*100))+"%] parsing ",objid,": ",objname," of type ",objtype

            # retrieving name
            n = getCleanName(objname,objid,objtype)

            # skip IDs
            if objid in skipIds:
                if DEBUG: print "    skipping because object ID is in skip list"
                nobj = None

            # skip types
            elif objtype in SKIP:
                if DEBUG: print "    skipping because type is in skip list"
                nobj = None
            
            # check if object was already processed, to workaround an ifcopenshell bug
            elif objid in processedIds:
                if DEBUG: print "    skipping because this object was already processed"

            else:
                # build shape
                shape = None
                if useShapes:
                    shape = getShape(obj,objid)

                '''# walls
                if objtype in ["IfcWallStandardCase","IfcWall"]:
                    nobj = makeWall(objid,shape,n)

                # windows
                elif objtype in ["IfcWindow","IfcDoor"]:
                    nobj = makeWindow(objid,shape,n)

                # structs
                elif objtype in ["IfcBeam","IfcColumn","IfcSlab","IfcFooting"]:
                    nobj = makeStructure(objid,shape,objtype,n)
                    
                # roofs
                elif objtype in ["IfcRoof"]:
                    nobj = makeRoof(objid,shape,n)
                    
                # furniture
                elif objtype in ["IfcFurnishingElement"]:
                    nobj = FreeCAD.ActiveDocument.addObject("Part::Feature",n)
                    nobj.Shape = shape'''
                    
                # sites
                if objtype in ["IfcSite"]:
                    nobj = makeSite(objid,shape,n)
                    
                # floors
                elif objtype in ["IfcBuildingStorey"]:
                    nobj = Arch.makeFloor(name=n)
                    nobj.Label = n
                    
                # floors
                elif objtype in ["IfcBuilding"]:
                    nobj = Arch.makeBuilding(name=n)
                    nobj.Label = n
                    
                # spaces
                elif objtype in ["IfcSpace"]:
                    nobj = makeSpace(objid,shape,n)
                    
                elif shape:
                    nobj = makeStructure(objid,shape,objtype,n)
                    '''# treat as dumb parts
                    if DEBUG: print "Fixme: Shape-containing object not handled: ",objid, " ", objtype 
                    nobj = FreeCAD.ActiveDocument.addObject("Part::Feature",n)
                    nobj.Label = n
                    nobj.Shape = shape'''
                    
                else:
                    # treat as meshes
                    if DEBUG: print "Warning: Object without shape: ",objid, " ", objtype
                    if hasattr(obj,"mesh"):
                        if not hasattr(obj.mesh, 'verts'):
                            obj = IfcImport.Get() # Get triangulated rep of same product
                        me,pl = getMesh(obj)
                        nobj = FreeCAD.ActiveDocument.addObject("Mesh::Feature",n)
                        nobj.Label = n
                        nobj.Mesh = me
                        nobj.Placement = pl
                    else:
                        if DEBUG: print "Error: Skipping object without mesh: ",objid, " ", objtype
                        nobj = None  # sonst aendern meine kommenden funktionen wenn ein obj hier rein kommt das letzte nobj !!!


                # Add additonal Attributes to nobj
                if nobj is not None:                
                  print ("    Add additonal Attributes to the new FreeCAD-Object")
                  # nobj: die Gefundenen Attribute als Dicionaries (App::PropertyMap) zuweisen
                  # PropertyMap wird nur von FeaturePython unterstuetzt     
                  if str(type(nobj)) == "<type 'FeaturePython'>":
                  # obiges liesse sich auch mit isinstance erreichen, aber wie?!? siehe naechsten zeilen
                  #if isinstance(nobj,FeaturePython):
                  #if isinstance(nobj,Part.PartFeature):
                    print ("      Found a " + str(type(nobj)) + " We are able to add PropertyMaps")
                    nobj = addObjectAttributes(nobj, objectAttributes)
                    nobj = addObjectMaterials(nobj, objectMaterials)
                    nobj = addObjectPropertySets(nobj, objectPropertySets)
                  else:
                    try:
                      print ("      Found: " + str(nobj.Name) + str(type(nobj)) + " It is not possible to add a PropertyMap to this object")
                      # exception wird ausgeloest wenn objekt kein name hat, diese abfangen !!!
                    except:
                      print ("      Found: " + str(type(nobj)) + " It is not possible to add a PropertyMap to this object")

                        
                # registering object number and parent
                if objparentid:
                    ifcParents[objid] = []
                    for p in objparentid:
                        ifcParents[objid].append([p,not (objtype in subtractiveTypes)])
                ifcObjects[objid] = nobj
                processedIds.append(objid)
            
            if IFCOPENSHELL5:
                if idx >= len(objects):
                    break
            else:
                if not IfcImport.Next():
                    break


        # processing non-geometry and relationships
        if DEBUG: print (" ")
        if DEBUG: print (" ")
        if DEBUG: print ("------------------ non-geometry and relationships---------")
        parents_temp = dict(ifcParents)
        import ArchCommands
        #print parents_temp

        while parents_temp:
            id, comps = parents_temp.popitem()
            for c in comps:
                parent_id = c[0]
                additive = c[1]
                
                if (id <= 0) or (parent_id <= 0):
                    # root dummy object
                    parent = None

                elif parent_id in ifcObjects:
                    parent = ifcObjects[parent_id]
                    # check if parent is a subtraction, if yes parent to grandparent
                    if parent_id in ifcParents:
                        for p in ifcParents[parent_id]:
                            if p[1] == False:
                                grandparent_id = p[0]
                                if grandparent_id in ifcObjects:
                                    parent = ifcObjects[grandparent_id]
                else:
                    # creating parent if needed
                    if IFCOPENSHELL5:
                        obj = ifc.by_id(parent_id)
                        parentid = int(str(obj).split("=")[0].strip("#"))
                        parentname = obj.get_argument(obj.get_argument_index("Name"))
                        parenttype = str(obj).split("=")[1].split("(")[0]
                    else:
                        obj = IfcImport.GetObject(parent_id)
                        parentid = obj.id
                        parentname = obj.name
                        parenttype = obj.type
                    #if DEBUG: print "["+str(int((float(idx)/num_lines)*100))+"%] parsing ",parentid,": ",parentname," of type ",parenttype
                    n = getCleanName(parentname,parentid,parenttype)
                    if parentid <= 0:
                        parent = None
                    elif parenttype == "IfcBuildingStorey":
                        parent = Arch.makeFloor(name=n)
                        parent.Label = n
                    elif parenttype == "IfcBuilding":
                        parent = Arch.makeBuilding(name=n)
                        parent.Label = n
                    elif parenttype == "IfcSite":
                        parent = Arch.makeSite(name=n)
                        parent.Label = n
                    elif parenttype == "IfcWindow":
                        parent = Arch.makeWindow(name=n)
                        parent.Label = n
                    elif parenttype == "IfcProject":
                        parent = None
                    else:
                        if DEBUG: print "Fixme: skipping unhandled parent: ", parentid, " ", parenttype
                        parent = None
                    # registering object number and parent
                    if not IFCOPENSHELL5:
                        if parent_ifcobj.parent_id > 0:
                                ifcParents[parentid] = [parent_ifcobj.parent_id,True]
                                parents_temp[parentid] = [parent_ifcobj.parent_id,True]
                        if parent and (not parentid in ifcObjects):
                            ifcObjects[parentid] = parent
            
                # attributing parent
                if parent and (id in ifcObjects):
                    if ifcObjects[id] and (ifcObjects[id].Name != parent.Name):
                        if additive:
                            if DEBUG: print "adding ",ifcObjects[id].Name, " to ",parent.Name
                            ArchCommands.addComponents(ifcObjects[id],parent)
                        else:
                            if DEBUG: print "removing ",ifcObjects[id].Name, " from ",parent.Name
                            ArchCommands.removeComponents(ifcObjects[id],parent)
        if not IFCOPENSHELL5:
            IfcImport.CleanUp()
        
    else:
        # use only the internal python parser
        
        FreeCAD.Console.PrintWarning(translate("Arch","IfcOpenShell not found or disabled, falling back on internal parser.\n"))
        schema=getSchema()
        if schema:
            if DEBUG: print "opening",filename,"..."
            ifcReader.DEBUG = DEBUG
            ifc = ifcReader.IfcDocument(filename,schema=schema)
        else:
            FreeCAD.Console.PrintWarning(translate("Arch","IFC Schema not found, IFC import disabled.\n"))
            return None
        t2 = time.time()
        if DEBUG: print "Successfully loaded",ifc,"in %s s" % ((t2-t1))
       
        # getting walls
        for w in ifc.getEnt("IfcWallStandardCase"):
            nobj = makeWall(w)
            
        # getting windows and doors
        for w in (ifc.getEnt("IfcWindow") + ifc.getEnt("IfcDoor")):
            nobj = makeWindow(w)
            
        # getting structs
        for w in (ifc.getEnt("IfcSlab") + ifc.getEnt("IfcBeam") + ifc.getEnt("IfcColumn") \
                  + ifc.getEnt("IfcFooting")):
            nobj = makeStructure(w)
             
        # getting floors
        for f in ifc.getEnt("IfcBuildingStorey"):
            group(f,ifc,"Floor")
            
        # getting buildings
        for b in ifc.getEnt("IfcBuilding"):
            group(b,ifc,"Building")
            
        # getting sites
        for s in ifc.getEnt("IfcSite"):
            group(s,ifc,"Site")

    if DEBUG: print "done parsing. Recomputing..."        
    FreeCAD.ActiveDocument.recompute()
    t3 = time.time()
    if DEBUG: print "done processing IFC file in %s s" % ((t3-t1))
    
    return None


def getCleanName(name,ifcid,ifctype):
    "Get a clean name from an ifc object"
    #print "getCleanName called",name,ifcid,ifctype
    n = name
    if not n:
        n = ifctype
    if PREFIX_NUMBERS:
        n = "ID"+str(ifcid)+" "+n
    #for c in ",.!?;:":
    #    n = n.replace(c,"_")
    return n


def makeWall(entity,shape=None,name="Wall"):
    "makes a wall in the freecad document"
    try:
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                body = FreeCAD.ActiveDocument.addObject("Part::Feature",name+"_body")
                body.Shape = shape
            else:
                body = FreeCAD.ActiveDocument.addObject("Mesh::Feature",name+"_body")
                body.Mesh = shape
            wall = Arch.makeWall(body,name=name)
            wall.Label = name
            if DEBUG: print "    made wall object ",entity,":",wall
            return wall
            
        # use internal parser
        if DEBUG: print "=====> making wall",entity.id
        placement = wall = wire = body = width = height = None
        placement = getPlacement(entity.ObjectPlacement)
        if DEBUG: print "    got wall placement",entity.id,":",placement
        width = entity.getProperty("Width")
        height = entity.getProperty("Height")
        if width and height:
                if DEBUG: print "    got width, height ",entity.id,":",width,"/",height
                for r in entity.Representation.Representations:
                    if r.RepresentationIdentifier == "Axis":
                        wire = getWire(r.Items,placement)
                        wall = Arch.makeWall(wire,width,height,align="Center",name="Wall"+str(entity.id))
        else:
                if DEBUG: print "    no height or width properties found..."
                for r in entity.Representation.Representations:
                    if r.RepresentationIdentifier == "Body":
                        for b in r.Items:
                            if b.type == "IFCEXTRUDEDAREASOLID":
                                norm = getVector(b.ExtrudedDirection)
                                norm.normalize()
                                wire = getWire(b.SweptArea,placement)
                                wall = Arch.makeWall(wire,width=0,height=b.Depth,name="Wall"+str(entity.id))
                                wall.Normal = norm
        if wall:
            if DEBUG: print "    made wall object  ",entity.id,":",wall
            return wall
        if DEBUG: print "    error: skipping wall",entity.id
        return None
    except:
        if DEBUG: print "    error: skipping wall",entity
        return None


def makeWindow(entity,shape=None,name="Window"):
    "makes a window in the freecad document"
    try:
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                window = Arch.makeWindow(name=name)
                window.Shape = shape
                window.Label = name
                if DEBUG: print "    made window object  ",entity,":",window
                return window
            
        # use internal parser
        if DEBUG: print "=====> making window",entity.id
        placement = window = wire = body = width = height = None
        placement = getPlacement(entity.ObjectPlacement)
        if DEBUG: print "got window placement",entity.id,":",placement
        width = entity.getProperty("Width")
        height = entity.getProperty("Height")
        for r in entity.Representation.Representations:
            if r.RepresentationIdentifier == "Body":
                for b in r.Items:
                    if b.type == "IFCEXTRUDEDAREASOLID":
                        wire = getWire(b.SweptArea,placement)
                        window = Arch.makeWindow(wire,width=b.Depth,name=objtype+str(entity.id))
        if window:
            if DEBUG: print "    made window object  ",entity.id,":",window
            return window
        if DEBUG: print "    error: skipping window",entity.id
        return None
    except:
        if DEBUG: print "    error: skipping window",entity
        return None


def makeStructure(entity,shape=None,ifctype=None,name="Structure"):
    "makes a structure in the freecad document"
    try:
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                body = FreeCAD.ActiveDocument.addObject("Part::Feature",name+"_FreeCAD_shape_body")
                body.Shape = shape
            else:
                body = FreeCAD.ActiveDocument.addObject("Mesh::Feature",name+"_body")
                body.Mesh = shape
            structure = Arch.makeStructure(body,name=name)
            structure.Label = name
            if ifctype == "IfcBeam":
                structure.Role = "Beam"
            elif ifctype == "IfcColumn":
                structure.Role = "Column"
            elif ifctype == "IfcSlab":
                structure.Role = "Slab"
            elif ifctype == "IfcFooting":
                structure.Role = "Foundation"
            if DEBUG: print "    made structure object  ",entity,":",structure," (type: ",ifctype,")"
            return structure
            
        # use internal parser
        if DEBUG: print "=====> making struct",entity.id
        placement = structure = wire = body = width = height = None
        placement = getPlacement(entity.ObjectPlacement)
        if DEBUG: print "got window placement",entity.id,":",placement
        width = entity.getProperty("Width")
        height = entity.getProperty("Height")
        for r in entity.Representation.Representations:
            if r.RepresentationIdentifier == "Body":
                for b in r.Items:
                    if b.type == "IFCEXTRUDEDAREASOLID":
                        wire = getWire(b.SweptArea,placement)
                        structure = Arch.makeStructure(wire,height=b.Depth,name=objtype+str(entity.id))
        if structure:
            if DEBUG: print "    made structure object  ",entity.id,":",structure
            return structure
        if DEBUG: print "    error: skipping structure",entity.id
        return None
    except:
        if DEBUG: print "    error: skipping structure",entity
        return None


def makeSite(entity,shape=None,name="Site"):
    "makes a site in the freecad document"
    try:
        body = None
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                body = FreeCAD.ActiveDocument.addObject("Part::Feature",name+"_body")
                body.Shape = shape
            else:
                body = FreeCAD.ActiveDocument.addObject("Mesh::Feature",name+"_body")
                body.Mesh = shape
        site = Arch.makeSite(name=name)
        site.Label = name
        if body:
            site.Terrain = body
        if DEBUG: print "    made site object  ",entity,":",site
        return site
    except:
        return None
        
def makeSpace(entity,shape=None,name="Space"):
    "makes a space in the freecad document"
    try:
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                space = Arch.makeSpace(name=name)
                space.Label = name
                body = FreeCAD.ActiveDocument.addObject("Part::Feature",name+"_body")
                body.Shape = shape
                space.Base = body
                body.ViewObject.hide()
                if DEBUG: print "    made space object  ",entity,":",space
                return space
    except:
        return None


def makeRoof(entity,shape=None,name="Roof"):
    "makes a roof in the freecad document"
    try:
        if shape:
            # use ifcopenshell
            if isinstance(shape,Part.Shape):
                roof = Arch.makeRoof(name=name)
                roof.Label = name
                roof.Shape = shape
                if DEBUG: print "    made roof object  ",entity,":",roof
                return roof
    except:
        return None

# geometry helpers ###################################################################

def getMesh(obj):
    "gets mesh and placement from an IfcOpenShell object"
    if IFCOPENSHELL5:
        return None,None
        print "fixme: mesh data not yet supported" # TODO implement this with OCC tessellate
    import Mesh
    meshdata = []
    print obj.mesh.faces
    print obj.mesh.verts
    f = obj.mesh.faces
    v = obj.mesh.verts
    for i in range(0, len(f), 3):
        face = []
        for j in range(3):
            vi = f[i+j]*3
            face.append([v[vi],v[vi+1],v[vi+2]])
        meshdata.append(face)
        print meshdata
    me = Mesh.Mesh(meshdata)
    # get transformation matrix
    m = obj.matrix
    mat = FreeCAD.Matrix(m[0], m[3], m[6], m[9],
                         m[1], m[4], m[7], m[10],
                         m[2], m[5], m[8], m[11],
                         0, 0, 0, 1)
    pl = FreeCAD.Placement(mat)
    return me,pl

def getShape(obj,objid):
    "gets a shape from an IfcOpenShell object"
    #print "retrieving shape from obj ",objid
    import Part
    sh=Part.Shape()
    brep_data = None
    importallshapsassimpleboxes = False
    #importallshapsassimpleboxes = True
    if importallshapsassimpleboxes:
      sh = Part.makeBox(1,1,1)
      return sh   
    if IFCOPENSHELL5:
        try:
            if hasattr(IfcImport,"SEW_SHELLS"):
                ss = IfcImport.SEW_SHELLS
            else:
                ss = 0
            if SEPARATE_OPENINGS and hasattr(IfcImport,"DISABLE_OPENING_SUBTRACTIONS"):
                if SEPARATE_PLACEMENTS and hasattr(IfcImport,"DISABLE_OBJECT_PLACEMENT"):
                    brep_data = IfcImport.create_shape(obj,IfcImport.DISABLE_OPENING_SUBTRACTIONS | IfcImport.DISABLE_OBJECT_PLACEMENT | ss)
                else:
                    brep_data = IfcImport.create_shape(obj,IfcImport.DISABLE_OPENING_SUBTRACTIONS | ss)
            else:
                if SEPARATE_PLACEMENTS and hasattr(IfcImport,"DISABLE_OBJECT_PLACEMENT"):
                    brep_data = IfcImport.create_shape(obj,IfcImport.DISABLE_OBJECT_PLACEMENT | ss)
                else:
                    brep_data = IfcImport.create_shape(obj, ss)
        except:
            print "Unable to retrieve shape data"
    else:
        brep_data = obj.mesh.brep_data
    if brep_data:
        try:
            if MAKETEMPFILES:
                import tempfile
                tf = tempfile.mkstemp(suffix=".brp")[1]
                of = pyopen(tf,"wb")
                of.write(brep_data)
                of.close()
                sh = Part.read(tf)
                os.remove(tf)
            else:
                sh.importBrepFromString(brep_data)
        except:
            print "    error: malformed shape"
            return None
        else:
            if IFCOPENSHELL5 and SEPARATE_PLACEMENTS:
                p = getPlacement(getAttr(obj,"ObjectPlacement"))
                if p:
                    sh.Placement = p
    if not sh.Solids:
        # try to extract a solid shape
        if sh.Faces:
            try:
                if DEBUG: print "    malformed solid. Attempting to fix..."
                shell = Part.makeShell(sh.Faces)
                if shell:
                    solid = Part.makeSolid(shell)
                    if solid:
                        sh = solid
            except:
                if DEBUG: print "    failed to retrieve solid from object ",objid
        else:
            if DEBUG: print "    object ", objid, " doesn't contain any geometry"
    if not IFCOPENSHELL5:
        m = obj.matrix
        mat = FreeCAD.Matrix(m[0], m[3], m[6], m[9],
                             m[1], m[4], m[7], m[10],
                             m[2], m[5], m[8], m[11],
                             0, 0, 0, 1)
        sh.Placement = FreeCAD.Placement(mat)
    # if DEBUG: print "getting Shape from ",obj 
    #print "getting shape: ",sh,sh.Solids,sh.Volume,sh.isValid(),sh.isNull()
    #for v in sh.Vertexes: print v.Point
    if sh:
        if not sh.isNull():
            return sh
    return None
    
def getPlacement(entity):
    "returns a placement from the given entity"
    if not entity: 
        return None
    if DEBUG: print "    getting placement ",entity
    if IFCOPENSHELL5:
        if isinstance(entity,int):
            entity = ifc.by_id(entity)
        entitytype = str(entity).split("=")[1].split("(")[0].upper()
        entityid = int(str(entity).split("=")[0].strip("#"))
    else:
        entitytype = entity.type.upper()
        entityid = entity.id
    pl = None
    if entitytype == "IFCAXIS2PLACEMENT3D":
        x = getVector(getAttr(entity,"RefDirection"))
        z = getVector(getAttr(entity,"Axis"))
        if not(x) or not(z):
            return None
        y = z.cross(x)
        loc = getVector(getAttr(entity,"Location"))
        m = DraftVecUtils.getPlaneRotation(x,y,z)
        pl = FreeCAD.Placement(m)
        pl.move(loc)
    elif entitytype == "IFCLOCALPLACEMENT":
        pl = getPlacement(getAttr(entity,"PlacementRelTo"))
        relpl = getPlacement(getAttr(entity,"RelativePlacement"))
        if pl and relpl:
            pl = relpl.multiply(pl)
        elif relpl:
            pl = relpl
    elif entitytype == "IFCCARTESIANPOINT":
        loc = getVector(entity)
        pl = FreeCAD.Placement()
        pl.move(loc)
    if DEBUG: print "    made placement for ",entityid,":",pl
    return pl
    
def getAttr(entity,attr):
    "returns the given attribute from the given entity"
    if IFCOPENSHELL5:
        if isinstance(entity,int):
            entity = ifc.by_id(entity)
        i = entity.get_argument_index(attr)
        return entity.get_argument(i)
    else:
        return getattr(entity,attr)
        
def getVector(entity):
    "returns a vector from the given entity"
    if not entity:
        return None
    if DEBUG: print "    getting point from ",entity
    if IFCOPENSHELL5:
        if isinstance(entity,int):
            entity = ifc.by_id(entity)
        entitytype = str(entity).split("=")[1].split("(")[0].upper()
    else:
        entitytype = entity.type.upper()
    if entitytype == "IFCDIRECTION":
        DirectionRatios = getAttr(entity,"DirectionRatios")
        if len(DirectionRatios) == 3:
            return FreeCAD.Vector(tuple(DirectionRatios))
        else:
            return FreeCAD.Vector(tuple(DirectionRatios+[0]))
    elif entitytype == "IFCCARTESIANPOINT":
        Coordinates = getAttr(entity,"Coordinates")
        if len(Coordinates) == 3:
            return FreeCAD.Vector(tuple(Coordinates))
        else:
            return FreeCAD.Vector(tuple(Coordinates+[0]))
    return None
    
# below is only used by the internal parser #########################################
 
def decode(name):
    "decodes encoded strings"
    try:
        decodedName = (name.decode("utf8"))
    except UnicodeDecodeError:
        try:
            decodedName = (name.decode("latin1"))
        except UnicodeDecodeError:
            FreeCAD.Console.PrintError(translate("Arch", "Error: Couldn't determine character encoding\n"))
            decodedName = name
    return decodedName

def getSchema():
    "retrieves the express schema"
    custom = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch").GetString("CustomIfcSchema","")
    if custom:
        if os.path.exists(custom):
            if DEBUG: print "Using custom schema: ",custom.split(os.sep)[-1]
            return custom
    p = None
    p = os.path.join(FreeCAD.ConfigGet("UserAppData"),SCHEMA.split(os.sep)[-1])
    if os.path.exists(p):
        return p
    import ArchCommands
    p = ArchCommands.download(SCHEMA)
    if p:
        return p
    return None 
    
def group(entity,ifc,mode=None):
    "gathers the children of the given entity"
    # only used by the internal parser
    
    try:
        if DEBUG: print "=====> making group",entity.id
        placement = None
        placement = getPlacement(entity.ObjectPlacement)
        if DEBUG: print "got cell placement",entity.id,":",placement
        subelements = ifc.find("IFCRELCONTAINEDINSPATIALSTRUCTURE","RelatingStructure",entity)
        subelements.extend(ifc.find("IFCRELAGGREGATES","RelatingObject",entity))
        elts = []
        for s in subelements:
            if hasattr(s,"RelatedElements"):
                s = s.RelatedElements
                if not isinstance(s,list): s = [s]
                elts.extend(s)
            elif hasattr(s,"RelatedObjects"):
                s = s.RelatedObjects
                if not isinstance(s,list): s = [s]
                elts.extend(s)
            elif hasattr(s,"RelatedObject"):
                s = s.RelatedObject
                if not isinstance(s,list): s = [s]
                elts.extend(s)
        print "found dependent elements: ",elts
        
        groups = [['Wall',['IfcWallStandardCase'],[]],
                  ['Window',['IfcWindow','IfcDoor'],[]],
                  ['Structure',['IfcSlab','IfcFooting','IfcBeam','IfcColumn'],[]],
                  ['Floor',['IfcBuildingStorey'],[]],
                  ['Building',['IfcBuilding'],[]],
                  ['Furniture',['IfcFurnishingElement'],[]]]
        
        for e in elts:
            for g in groups:
                for t in g[1]:
                    if e.type.upper() == t.upper():
                        if hasattr(FreeCAD.ActiveDocument,g[0]+str(e.id)):
                            g[2].append(FreeCAD.ActiveDocument.getObject(g[0]+str(e.id)))
        print "groups:",groups

        comps = []
        if CREATE_IFC_GROUPS:
            if DEBUG: print "creating subgroups"
            for g in groups:
                if g[2]:
                    if g[0] in ['Building','Floor']:
                        comps.extend(g[2])
                    else:
                        fcg = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup",g[0]+"s")
                        for o in g[2]:
                            fcg.addObject(o)
                        comps.append(fcg)
        else:
            for g in groups:
                comps.extend(g[2])

        label = entity.Name
        name = mode + str(entity.id)
        cell = None
        if mode == "Site":
            cell = Arch.makeSite(comps,name=name)
        elif mode == "Floor":
            cell = Arch.makeFloor(comps,name=name)
        elif mode == "Building":
            cell = Arch.makeBuilding(comps,name=name)
        if label and cell:
            cell.Label = label
    except:
        if DEBUG: print "error: skipping group ",entity.id
        
def getWire(entity,placement=None):
    "returns a wire (created in the freecad document) from the given entity"
    # only used by the internal parser
    if DEBUG: print "making Wire from :",entity
    if not entity: return None
    if entity.type == "IFCPOLYLINE":
        pts = []
        for p in entity.Points:
            pts.append(getVector(p))
        return Draft.getWire(pts,placement=placement)
    elif entity.type == "IFCARBITRARYCLOSEDPROFILEDEF":
        pts = []
        for p in entity.OuterCurve.Points:
            pts.append(getVector(p))
        return Draft.getWire(pts,closed=True,placement=placement)

    
# EXPORT ##########################################################

def export(exportList,filename):
    "called when freecad exports a file"
    try:
        import IfcImport as ifcw
    except:
        try:
            import ifc_wrapper as ifcw
        except:
            FreeCAD.Console.PrintError(translate("Arch","Error: IfcOpenShell is not installed\n"))
            print """importIFC: ifcOpenShell is not installed. IFC export is unavailable.
                    Note: IFC export currently requires an experimental version of IfcOpenShell
                    available from https://github.com/aothms/IfcOpenShell"""
            return

    if (not hasattr(ifcw,"IfcFile")) and (not hasattr(ifcw,"file")):
        FreeCAD.Console.PrintError(translate("Arch","Error: your IfcOpenShell version is too old\n"))
        print """importIFC: The version of ifcOpenShell installed on this system doesn't
                 have IFC export capabilities. IFC export currently requires an experimental 
                 version of IfcOpenShell available from https://github.com/aothms/IfcOpenShell"""
        return
    import ifcWriter,Arch,Draft

    # creating base IFC project
    getConfig()
    ifcWriter.PRECISION = Draft.precision()
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
    scaling = p.GetFloat("IfcScalingFactor",1.0)
    exporttxt = p.GetBool("IfcExportList",False)
    forcebrep = p.GetBool("ifcExportAsBrep",False)
    application = "FreeCAD"
    ver = FreeCAD.Version()
    version = ver[0]+"."+ver[1]+" build"+ver[2]
    owner = FreeCAD.ActiveDocument.CreatedBy
    company = FreeCAD.ActiveDocument.Company
    project = FreeCAD.ActiveDocument.Name
    ifc = ifcWriter.IfcDocument(filename,project,owner,company,application,version)
    txt = []

    # get all children and reorder list to get buildings and floors processed first
    objectslist = Draft.getGroupContents(exportList,walls=True,addgroups=True)
    objectslist = Arch.pruneIncluded(objectslist)

    sites = []
    buildings = []
    floors = []
    groups = {}
    others = []
    for obj in objectslist:
        otype = Draft.getType(obj)
        if otype == "Site":
            sites.append(obj)
        elif otype == "Building":
            buildings.append(obj)
        elif otype == "Floor":
            floors.append(obj)
        elif otype == "Group":
            groups[obj.Name] = []
        else:
            others.append(obj)
    objectslist = buildings + floors + others
    if DEBUG: print "adding ", len(objectslist), " objects"
        
    global unprocessed
    unprocessed = []

    # process objects
    for obj in objectslist:

        otype = Draft.getType(obj)
        name = str(obj.Label)
        parent = Arch.getHost(obj)
        gdata = None
        fdata = None
        placement = None
        color = None
        representation = None
        descr = None
        extra = None
            
        # setting the IFC type
        if hasattr(obj,"Role"):
            ifctype = obj.Role.replace(" ","")
        else:
            ifctype = otype
        if ifctype == "Foundation":
            ifctype = "Footing"
        elif ifctype == "Rebar":
            ifctype = "ReinforcingBar"
        elif ifctype in ["Part","Undefined"]:
            ifctype = "BuildingElementProxy"
            
        # getting the "Force BREP" flag
        brepflag = False
        if hasattr(obj,"IfcAttributes"):
            if "ForceBrep" in obj.IfcAttributes.keys():
                if obj.IfcAttributes["ForceBrep"] == "True":
                    brepflag = True

        if DEBUG: print "Adding " + obj.Label + " as Ifc" + ifctype
                 
        # writing IFC data 
        if obj.isDerivedFrom("App::DocumentObjectGroup"):
            
            # getting parent building
            if parent:
                parent = ifc.findByName("IfcBuilding",str(parent.Label))

            if otype == "Site":
                print "   Skipping (not implemented yet)" # TODO manage sites
            elif otype == "Building":
                ifc.addBuilding( name=name )
            elif otype == "Floor":
                ifc.addStorey( building=parent, name=name )

        elif obj.isDerivedFrom("Part::Feature"):

            # get color
            if FreeCAD.GuiUp:
                color = obj.ViewObject.ShapeColor[:3]

            # get parent floor
            if parent:
                parent = ifc.findByName("IfcBuildingStorey",str(parent.Label))

            # get representation
            if (not forcebrep) and (not brepflag):
                gdata = getIfcExtrusionData(obj,scaling,SEPARATE_OPENINGS)
                #if DEBUG: print "   extrusion data for ",obj.Label," : ",gdata
            if not gdata:
                fdata = getIfcBrepFacesData(obj,scaling)
                #if DEBUG: print "   brep data for ",obj.Label," : ",fdata
                if not fdata:
                    if obj.isDerivedFrom("Part::Feature"):
                        print "   Error retrieving the shape of object ", obj.Label
                        unprocessed.append(obj)
                        continue
                    else:
                        if DEBUG: print "   No geometry"
                else:
                    if DEBUG: print "   Brep"
            else:
                if DEBUG: print "   Extrusion"
            if gdata:
                # gdata = [ type, profile data, extrusion data, placement data ]
                placement = ifc.addPlacement(origin=gdata[3][0],xaxis=gdata[3][1],zaxis=gdata[3][2])
                if gdata[0] == "polyline":
                    representation = ifc.addExtrudedPolyline(gdata[1], gdata[2], color=color)
                elif gdata[0] == "circle":
                    representation = ifc.addExtrudedCircle(gdata[1], gdata[2], color=color)
                elif gdata[0] == "ellipse":
                    representation = ifc.addExtrudedEllipse(gdata[1], gdata[2], color=color)
                elif gdata[0] == "composite":
                    representation = ifc.addExtrudedCompositeCurve(gdata[1], gdata[2], color=color)
                else:
                    print "debug: unknow extrusion type"
            elif fdata:
                representation = [ifc.addFacetedBrep(f, color=color) for f in fdata]

            # create ifc object
            ifctype = "Ifc" + ifctype
            if hasattr(obj,"Description"):
                descr = obj.Description
            if otype == "Wall":
                if gdata:
                    if gdata[0] == "polyline":
                        ifctype = "IfcWallStandardCase"
            elif otype == "Structure":
                if ifctype in ["IfcSlab","IfcFooting"]:
                    extra = ["NOTDEFINED"]
            elif otype == "Window":
                extra = [obj.Width.Value*scaling, obj.Height.Value*scaling]
            elif otype == "Space":
                extra = ["ELEMENT","INTERNAL",getIfcElevation(obj)]
            elif otype == "Part":
                extra = ["ELEMENT"]
            if not ifctype in supportedIfcTypes:
                if DEBUG: print "   Type ",ifctype," is not supported yet. Exporting as IfcBuildingElementProxy instead"
                ifctype = "IfcBuildingElementProxy"
                extra = ["ELEMENT"]
                
            product = ifc.addProduct( ifctype, representation, storey=parent, placement=placement, name=name, description=descr, extra=extra )

            if product:
                # removing openings
                if SEPARATE_OPENINGS and gdata:
                    for o in obj.Subtractions:
                        print "Subtracting ",o.Label
                        fdata = getIfcBrepFacesData(o,scaling,sub=True)
                        representation = [ifc.addFacetedBrep(f, color=color) for f in fdata]
                        p2 = ifc.addProduct( "IfcOpeningElement", representation, storey=product, placement=None, name=str(o.Label), description=None)

                # writing text log
                spacer = ""
                for i in range(36-len(obj.Label)):
                    spacer += " "
                txt.append(obj.Label + spacer + ifctype)
                
                # adding object to group, if any
                for g in groups.keys():
                    group = FreeCAD.ActiveDocument.getObject(g)
                    if group:
                        for o in group.Group:
                            if o.Name == obj.Name:
                                groups[g].append(product)
                
            else:
                unprocessed.append(obj)
        else:
            if DEBUG: print "Object type ", otype, " is not supported yet."

    # processing groups
    for name,entities in groups.iteritems():
        if entities:
            o = FreeCAD.ActiveDocument.getObject(name)
            if o:
                if DEBUG: print "Adding group ", o.Label, " with ",len(entities)," elements"
                grp = ifc.addGroup( entities, o.Label )
            
    ifc.write()

    if exporttxt:
        import time, os
        txtstring = "List of objects exported by FreeCAD in file\n"
        txtstring += filename + "\n"
        txtstring += "On " + time.ctime() + "\n"
        txtstring += "\n"
        txtstring += str(len(txt)) + " objects exported:\n"
        txtstring += "\n"
        txtstring += "Nr      Name                          Type\n"
        txtstring += "\n"
        for i in range(len(txt)):
            idx = str(i+1)
            sp = ""
            for j in range(8-len(idx)):
                sp += " "
            txtstring += idx + sp + txt[i] + "\n"
        txtfile = os.path.splitext(filename)[0]+".txt"
        f = pyopen(txtfile,"wb")
        f.write(txtstring)
        f.close()

    FreeCAD.ActiveDocument.recompute()
    
    if unprocessed:
        print ""
        print "WARNING: " + str(len(unprocessed)) + " objects were not exported (stored in importIFC.unprocessed):"
        for o in unprocessed:
            print "    " + o.Label


def getTuples(data,scale=1,placement=None,normal=None,close=True):
    """getTuples(data,[scale,placement,normal,close]): returns a tuple or a list of tuples from a vector
    or from the vertices of a shape. Scale can indicate a scale factor"""
    rnd = False
    import Part
    if isinstance(data,FreeCAD.Vector):
        if placement:
            data = placement.multVec(data)
        if rnd:
            data = DraftVecUtils.rounded(data)
        return (data.x*scale,data.y*scale,data.z*scale)
    elif isinstance(data,Part.Shape):
        t = []
        if len(data.Wires) == 1:
            import Part,DraftGeomUtils
            data = Part.Wire(DraftGeomUtils.sortEdges(data.Wires[0].Edges))
            verts = data.Vertexes
            try:
                c = data.CenterOfMass
                v1 = verts[0].Point.sub(c)
                v2 = verts[1].Point.sub(c)
                if DraftVecUtils.angle(v2,v1,normal) >= 0:
                    # inverting verts order if the direction is couterclockwise
                    verts.reverse()
            except:
                pass
            for v in verts:
                pt = v.Point
                if placement:
                    if not placement.isNull():
                        pt = placement.multVec(pt)
                if rnd:
                    pt = DraftVecUtils.rounded(pt)
                t.append((pt.x*scale,pt.y*scale,pt.z*scale))

            if close: # faceloops must not be closed, but ifc profiles must.
                t.append(t[0])
        else:
            print "Arch.getTuples(): Wrong profile data"
        return t

def getIfcExtrusionData(obj,scale=1,nosubs=False):
    """getIfcExtrusionData(obj,[scale,nosubs]): returns a closed path (a list of tuples), a tuple expressing an extrusion
    vector, and a list of 3 tuples for base position, x axis and z axis. Or returns None, if a base loop and 
    an extrusion direction cannot be extracted. Scale can indicate a scale factor."""
    
    CURVEMODE = "PARAMETER" # For trimmed curves. CARTESIAN or PARAMETER
    
    if hasattr(obj,"Additions"):
        if obj.Additions:
            # TODO provisorily treat objs with additions as breps
            return None
    if hasattr(obj,"Subtractions") and not nosubs:
        if obj.Subtractions:
            return None
    if hasattr(obj,"Proxy"):
        if hasattr(obj.Proxy,"getProfiles"):
            p = obj.Proxy.getProfiles(obj,noplacement=True)
            v = obj.Proxy.getExtrusionVector(obj,noplacement=True)
            if (len(p) == 1) and v:
                p = p[0]
                r = FreeCAD.Placement()
                #b = p.CenterOfMass
                r = obj.Proxy.getPlacement(obj)
                #b = obj.Placement.multVec(FreeCAD.Vector())
                #r.Rotation = DraftVecUtils.getRotation(v,FreeCAD.Vector(0,0,1))
                d = [r.Base,DraftVecUtils.rounded(r.Rotation.multVec(FreeCAD.Vector(1,0,0))),DraftVecUtils.rounded(r.Rotation.multVec(FreeCAD.Vector(0,0,1)))]
                #r = r.inverse()
                #print "getExtrusionData: computed placement:",r
                import Part
                if len(p.Edges) == 1:
                    if isinstance(p.Edges[0].Curve,Part.Circle):
                        # Circle profile
                        r1 = p.Edges[0].Curve.Radius*scale
                        return "circle", [getTuples(p.Edges[0].Curve.Center,scale), r1], getTuples(v,scale), d
                    elif isinstance(p.Edges[0].Curve,Part.Ellipse):
                        # Ellipse profile
                        r1 = p.Edges[0].Curve.MajorRadius*scale
                        r2 = p.Edges[0].Curve.MinorRadius*scale
                        return "ellipse", [getTuples(p.Edges[0].Curve.Center,scale), r1, r2], getTuples(v,scale), d
                curves = False
                for e in p.Edges:
                    if isinstance(e.Curve,Part.Circle):
                        curves = True
                    elif not isinstance(e.Curve,Part.Line):
                        print "Arch.getIfcExtrusionData: Warning: unsupported edge type in profile"
                if curves:
                    # Composite profile
                    ecurves = []
                    last = None
                    import DraftGeomUtils
                    edges = DraftGeomUtils.sortEdges(p.Edges)
                    for e in edges:
                        if isinstance(e.Curve,Part.Circle):
                            import math
                            follow = True
                            if last:
                                if not DraftVecUtils.equals(last,e.Vertexes[0].Point):
                                    follow = False
                                    last = e.Vertexes[0].Point
                                else:
                                    last = e.Vertexes[-1].Point
                            else:
                                last = e.Vertexes[-1].Point
                            p1 = math.degrees(-DraftVecUtils.angle(e.Vertexes[0].Point.sub(e.Curve.Center)))
                            p2 = math.degrees(-DraftVecUtils.angle(e.Vertexes[-1].Point.sub(e.Curve.Center)))
                            da = DraftVecUtils.angle(e.valueAt(e.FirstParameter+0.1).sub(e.Curve.Center),e.Vertexes[0].Point.sub(e.Curve.Center))
                            if p1 < 0: 
                                p1 = 360 + p1
                            if p2 < 0:
                                p2 = 360 + p2
                            if da > 0:
                                follow = not(follow)
                            if CURVEMODE == "CARTESIAN":
                                # BUGGY
                                p1 = getTuples(e.Vertexes[0].Point,scale)
                                p2 = getTuples(e.Vertexes[-1].Point,scale)
                            ecurves.append(["arc",getTuples(e.Curve.Center,scale),e.Curve.Radius*scale,[p1,p2],follow,CURVEMODE])
                        else:
                            verts = [vertex.Point for vertex in e.Vertexes]
                            if last:
                                if not DraftVecUtils.equals(last,verts[0]):
                                    verts.reverse()
                                    last = e.Vertexes[0].Point
                                else:
                                    last = e.Vertexes[-1].Point
                            else:
                                last = e.Vertexes[-1].Point
                            ecurves.append(["line",[getTuples(vert,scale) for vert in verts]])
                    return "composite", ecurves, getTuples(v,scale), d
                else:
                    # Polyline profile
                    return "polyline", getTuples(p,scale), getTuples(v,scale), d
    return None   
    
def getIfcBrepFacesData(obj,scale=1,sub=False,tessellation=1):
    """getIfcBrepFacesData(obj,[scale,tesselation]): returns a list(0) of lists(1) of lists(2) of lists(3), 
    list(3) being a list of vertices defining a loop, list(2) describing a face from one or 
    more loops, list(1) being the whole solid made of several faces, list(0) being the list
    of solids inside the object. Scale can indicate a scaling factor. Tesselation is the tesselation
    factor to apply on curved faces."""
    shape = None
    if sub:
        if hasattr(obj,"Proxy"):
            if hasattr(obj.Proxy,"getSubVolume"):
                shape = obj.Proxy.getSubVolume(obj)
    if not shape:
        if hasattr(obj,"Shape"):
            if obj.Shape:
                if not obj.Shape.isNull():
                    if obj.Shape.isValid():
                        shape = obj.Shape
    if shape:
        import Part
        sols = []
        for sol in shape.Solids:
            s = []
            curves = False
            for face in sol.Faces:
                for e in face.Edges:
                    if not isinstance(e.Curve,Part.Line):
                        curves = True
            if curves:
                tris = sol.tessellate(tessellation)
                for tri in tris[1]:
                    f = []
                    for i in tri:
                        f.append(getTuples(tris[0][i],scale))
                    s.append([f])
            else:
                for face in sol.Faces:
                    f = []
                    f.append(getTuples(face.OuterWire,scale,normal=face.normalAt(0,0),close=False))
                    for wire in face.Wires:
                        if wire.hashCode() != face.OuterWire.hashCode():
                            f.append(getTuples(wire,scale,normal=DraftVecUtils.neg(face.normalAt(0,0)),close=False))
                    s.append(f)
            sols.append(s)
        return sols
    return None
    
def getIfcElevation(obj):
    """getIfcElevation(obj): Returns the lowest height (Z coordinate) of this object"""
    if obj.isDerivedFrom("Part::Feature"):
        b = obj.Shape.BoundBox
        return b.ZMin
    return 0


def explore(filename=None):
    "explore the contents of an ifc file in a Qt dialog"
    if not filename:
        from PySide import QtGui
        filename = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(),'IFC files','*.ifc')
        if filename:
            filename = filename[0]
    if filename:
        import ifcReader
        getConfig()
        schema=getSchema()
        ifcReader.DEBUG = DEBUG
        d = ifcReader.explorer(filename,schema)
        d.show()
        return d



###############################################################################################################
###############################################################################################################
###############################################################################################################
#Methoden bhb
###############################################################################################################
def getObjectAttributes(objid, objtype, objname):
  """ Dictionary objectAttributes 
  
  """
  if objname == None:
    objname = ''
  objectAttributes = {"ID":str(objid), "Type":objtype, "Name":objname}
  #print objectAttributes
  return objectAttributes



def getObjectMaterials(obj, materialrelations):
  """ Dictionary objectMaterials mit key Materialname value Dicke (nur bei IfcMaterialLayer sonst leerer String)
  
  """
  if len(materialrelations) == 0:
    print "Keine Materialdefinitionen in der Datei vorhanden!"
    return None
  objectMaterials = {}
  materiallayerlist = []
  materiallist = []
  for p in materialrelations:
    for c in getAttr(p,"RelatedObjects"):
      if str(obj) == str(c):
        #print c                  # IfcSlab, IfcWall, ...
        #print p                  # IfcRelAssociatesMaterial
        #print p.get_argument(5)   # see if ...
        if p.get_argument(5) is not None:  # could be none if Allplan 2012 and no Material is definend (Dachhaut)
          if p.get_argument(5).is_a("IfcMaterialLayerSetUsage"):
            #print p.get_argument(5).get_argument(0)                      # IfcMaterialLayerSet
            #print p.get_argument(5).get_argument(0).get_argument(0)      # List IfcMaterialLayer
            materiallayerlist = p.get_argument(5).get_argument(0).get_argument(0)
          elif p.get_argument(5).is_a("IfcMaterialLayerSet"):
            #print p.get_argument(5).get_argument(0)                      # List IfcMaterialLayer
            materiallayerlist = p.get_argument(5).get_argument(0)
          elif p.get_argument(5).is_a("IfcMaterialList"):
            #print p.get_argument(5).get_argument(0)                      # List IfcMaterial
            materiallist = p.get_argument(5).get_argument(0)
          elif p.get_argument(5).is_a("IfcMaterial"):
            #print p.get_argument(5).get_argument(0)                      # String Material
            materiallist.append(p.get_argument(5))
          else:
            print (p.get_argument(5).is_a() + " is not implemented")
            #print p.get_argument(5)
  if len(materiallist) > 0 and len(materiallayerlist)  == 0:
    #print "materiallist hat eintraege!!"
    # add materiallist to dict
    for m in materiallist:
      objectMaterials[m.get_argument(0)] = 'not defiened' 
  elif len(materiallayerlist) > 0 and len(materiallist) == 0:
    #print "materiallayerlist hat eintraege!!"
    for m in materiallayerlist:
      #print m                                    # IfcMaterialLayer
      #print m.get_argument(0)                    # IfcMaterial
      #print ( m.get_argument(0).get_argument(0) + ' --> ' +  str(m.get_argument(1)) )    # material + thickness 
      if m.get_argument(1) is not None:
        objectMaterials[m.get_argument(0).get_argument(0)] = str(m.get_argument(1))
      else:
        objectMaterials[m.get_argument(0).get_argument(0)] = 'not defiened'
  elif len(materiallist) == 0 and len(materiallayerlist)  == 0:
    print "Keine Materialdefinition fuer dieses Objekt gefunden!!"
    return None
  else:
    print "Etwas ist bei Auslesen des Materials schiefgelaufen, es hat Materiallist und materiallayerlist"
    #print materiallist
    #print materiallayerlist
    
  # print objectMaterials
  #for m in objectMaterials:
  #  print (m + ' --> ' + objectMaterials[m])
  
  return objectMaterials



def getObjectPropertySets(obj, propertyrelations):
  """ liste objectProperties mit tupels aus String propertysetname und Dictionary mit Inhalt 
  
  """
  if len(propertyrelations) == 0:
    print "Keine Propertydefinitionen in der Datei vorhanden!"
    return None
  
  objectProperties = []
  
  # IfcElementQuantity and IfcPropertySet
  quantityentrylist = []
  propertyentrylist = []
  for p in propertyrelations:
    for c in getAttr(p,"RelatedObjects"):
      if str(obj) == str(c):
        #print c
        #print p
        #print p.get_argument(5)   # ist der gesamte entity
        if p.get_argument(5).is_a("IfcElementQuantity"):
          quantityentrylist.append(p.get_argument(5))
        elif p.get_argument(5).is_a("IfcPropertySet"):
          propertyentrylist.append(p.get_argument(5))
        else:
          print (p.get_argument(5).is_a() + " is not implemented: Nur IfcElementQuantity und IfcPropertySet")
          #print p.get_argument(5)
         
  for qe in quantityentrylist:
    #print qe
    objectProperties.append(getQuantities(qe))
  for pse in propertyentrylist:
    #print pse
    objectProperties.append(getPropertryset(pse))
  
  if len(objectProperties) == 0:
    print "Keine PropertySets und ElementQuantities fuer dieses Objekt gefunden!!"
    return None

  # print objectProperties
  '''print ("    Found the following PropertySets and ElementQuantitys")
  for o in objectProperties:
    print ('        ' + o[0])
    for k in o[1]:
      print ( '            ' + k + '  -->  ' + o[1][k] )
  '''
  
  return (objectProperties)


###################################################################################
def getQuantities(qe):
  """Liste von ElementQuantityEntries wird uebergeben. 
  
  Tupel welches string mit quantityname und dictionary mit quantityentries (key, value) wird zurueckuebergeben
  """
  #print qe     # elementquantityentry
  gp = {}
  quantitysetname = ''
  # 0  UUID
  # 1  Verweis auf Ownerhistory
  # 2  ElementQuantityName (String)
  # 3  ?
  # 4  ?
  # 5  zugehoerige Entities (List)
  quantitysetname = qe.get_argument(2)
  #print ("    Found ElementQuantity: " + propertysetname)
  quantitylist = qe.get_argument(5)
  for q in quantitylist:
    #print q
    #print q.get_argument(0)+'='+str(q.get_argument(3))+' '+q.get_argument(2).get_argument(3)
    # eintraege in dictionary schreiben
    #Values of Add::PropertyMap must be Strings
    gp[q.get_argument(0)] = str(q.get_argument(3))
  #print gp
  #print quantitysetname
  return (quantitysetname,gp)



def getPropertryset(pse):
  """Liste von PropertySetEntries wird uebergeben. 
  
  Tupel welches string mit setname und dictionary mit setentries (key, value) wird zurueckuebergeben
  """
  #print pse     # properysetentry
  gp = {}
  propertysetname = ''
  # 0  UUID
  # 1  Verweis auf Ownerhistory
  # 2  PropertySetName (String)
  # 3  ?
  # 4  zugehoerige Entities (List)
  propertysetname = pse.get_argument(2)
  #print ("    Found PropertySet: " + propertysetname)
  propertysetlist = pse.get_argument(4)
  for q in propertysetlist:
    if q.is_a("IfcComplexProperty"):
       #print ("    Found IfcComplexProperty, alle der Gesamtwand zugeordnet")
       # bei waenden hat jeder layer seine eigenen props
       # da ich nur ein layer habe ist es egal
       #print q   # ist der gesamte entity
       # 0  ComplexPropertyName (String)
       # 1  String
       # 2  String
       # 3  zugehoerige Entities (List)
       #print q.get_argument(0)
       #print q.get_argument(1)
       #print q.get_argument(2)
       for e in q.get_argument(3):
         if e.is_a("IfcPropertySingleValue"):
           gp = getPropertryEntry(e, gp)
         else:
           print "Not implemented yet!"
           print e
    elif q.is_a("IfcPropertySingleValue"):
      gp = getPropertryEntry(q, gp)
    else:
       print "Not implemented yet! Only IfcPropertySingleValue and IfcComplexProperty are is implemented"
       print q
  #print gp
  #print propertysetname
  return (propertysetname, gp)



def getPropertryEntry(pe, gp):
  """extract keys and values from IfcPropertySingleValue
  
  """
  
  # entity
  #print pe   # ist der gesamte entity
  # 0  Key 
  # 1  ?
  # 2  Value 
  # 3  ?
  
  # key
  #print pe.get_argument(0)  # key
  pe_key = pe.get_argument(0)
  
  # value
  #print ("       Found Property: " + str(pe.get_argument(2)))
  # Values of Add::PropertyMap must be Strings
  if pe.get_argument(2) == None:
    gp[pe_key] = ""
  elif pe.get_argument(2).is_a("IfcDescriptiveMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcLabel"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcText"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcPositiveLengthMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcInteger"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcBoolean"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcLengthMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcAreaMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcVolumeMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcPlaneAngleMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcThermalTransmittanceMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcCountMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcMassMeasure"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcLogical"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcIdentifier"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  elif pe.get_argument(2).is_a("IfcReal"):
    gp[pe_key] = str(pe.get_argument(2).get_argument(0))
  else:
    print pe.get_argument(2)
    print "Not implemented!"
  return (gp)  


###################################################################################
def  addObjectAttributes(nobj, objectAttributes):
  """nobj: Attribute als Dicionariy (App::PropertyMap) zuweisen

  """
  if objectAttributes == None:
    print "      No Attributes added."
    return(nobj)

  if hasattr(nobj, "IfcImportedAttributes"):
    print "      Object allready has IfcImportedAttributes."
    return(nobj)    

  nobj.addProperty("App::PropertyMap","IfcImportedAttributes","IfcImportedAttributes","dictionary of imported standard object attributes")
  nobj.IfcImportedAttributes = objectAttributes
  print "      added: Standard Attributes"

  # solange die Dictionaries nicht angezeigt werden konnen fuege auch Attribute hinzu, die direkt angezeigt werden
  nobj.addProperty("App::PropertyString","IfcObjectType","IfcAttributesTMP","string of imported IfcType")
  nobj.IfcObjectType = objectAttributes['Type']
  
  return(nobj)



def addObjectMaterials(nobj, objectMaterials):
  """nobj: die Gefundenen materials (objectMaterials) als Dicionariy (App::PropertyMap) zuweisen

  """
  if objectMaterials == None:
    print "      No Materials added."
    return(nobj)
  
  if hasattr(nobj, "IfcImportedMaterials"):
    print "      Object allready has IfcImportedMaterials."
    return(nobj)    

  nobj.addProperty("App::PropertyMap","IfcImportedMaterials","IfcImportedMaterials","dictionary of imported object materials")
  nobj.IfcImportedMaterials = objectMaterials
  print "      added: Materials"
  
  # solange die Dictionaries nicht angezeigt werden konnen fuege auch Attribute hinzu, die direkt angezeigt werden (das erste Material)
  nobj.addProperty("App::PropertyString","IfcMaterial","IfcAttributesTMP","string of imported Material (the first (ABC) if more than one)")
  for k in sorted(objectMaterials):
    nobj.IfcMaterial = k
  
  return(nobj)



def addObjectPropertySets(nobj, objectPropertySets):
  """nobj: die Gefundenen Attribute (objectProperties) als Dicionaries (App::PropertyMap) zuweisen

  """
  if objectPropertySets == None:
    print "      No Properties added."
    return(nobj)
  
  '''
  # Allgemeine Properties
  #nobj.addProperty("App::PropertyMap","IfcObjectProp","IfcObjectProp","dictionary of imported properties")
  #nobj.IfcObjectProp = getIfcObjProperties(objname,objid,objtype)

  print ("    " + str(len(objectProperties)) + " PropertySets und Quantities wurden zur Zuweisung von PropertyMaps uebergeben")
  for io, o in enumerate(objectProperties):
    #print ( 'Name dieses Properties ' + str(io) + ' ist ' + o[0] )
    #propertymapname = ('PropertyMap' + str(io))
    #print propertymapname
    if len(o[1]) > 0:
      if io == 0:
        nobj.addProperty("App::PropertyMap","IfcElementQuantitySet","IfcElementQuantitySet","dictionary of imported object properties")
        nobj.IfcElementQuantitySet = o[1]
      if io == 1:
        nobj.addProperty("App::PropertyMap","MyPropertyMap2","MyPropertyMap2","dictionary of imported object properties")
        nobj.MyPropertyMap2 = o[1]
      if io == 2:
        nobj.addProperty("App::PropertyMap","MyPropertyMap3","MyPropertyMap3","dictionary of imported object properties")
        nobj.MyPropertyMap3 = o[1]
      if io == 3:
        nobj.addProperty("App::PropertyMap","MyPropertyMap4","MyPropertyMap4","dictionary of imported object properties")
        nobj.MyPropertyMap4 = o[1]
      else:
        print ("only 4 PropertyMaps implemented")

      # pendent ueber schleife alle objectProperties vorhandenen zuweisen
      #nobj.addProperty("App::PropertyMap",propertymapname,propertymapname,"dictionary of imported object properties")
      #nobj.('PropertyMap' + str(io)) = o[1]
  '''
  
  # All Properties in one Dictionary ohne Setnamen
  #print ("    AllProperties")
  AllProperties = {}
  for o in objectPropertySets:
    for k in o[1]:
      AllProperties[k] =  o[1][k]
  for k in AllProperties:
    pass
    #print ( '            ' + k + '  -->  ' + AllProperties[k] )
  
  if hasattr(nobj, "IfcImportedProperties"):
    print "      Object allready has IfcImportedProperties."
    return(nobj)    
  
  nobj.addProperty("App::PropertyMap","IfcImportedProperties","IfcImportedProperties","dictionary of imported object properties")
  nobj.IfcImportedProperties = AllProperties
  print "      added: Properties"
  
  # Ein dictionary mit unterdictionarys waere auch ne idee, aber die FreeCAD PropertyMap unterstuetzt nur Werte des Types String und Unicode
  
  # solange die Dictionaries nicht angezeigt werden konnen fuege auch Attribute hinzu, die direkt angezeigt werden
  if 'NetVolume' in nobj.IfcImportedProperties:
    nobj.addProperty("App::PropertyString","IfcNetVolume","IfcElementQuantity","string of imported NetVolume (if available)")
    nobj.IfcNetVolume = nobj.IfcImportedProperties['NetVolume']
  if 'GrossVolume' in nobj.IfcImportedProperties:
    nobj.addProperty("App::PropertyString","IfcGrossVolume","IfcElementQuantity","string of imported GrossVolume (if available)")
    nobj.IfcGrossVolume = nobj.IfcImportedProperties['GrossVolume']
  if 'GrossSideArea' in nobj.IfcImportedProperties:
    nobj.addProperty("App::PropertyString","IfcGrossSideArea","IfcElementQuantity","string of imported GrossSideArea (if available)")
    nobj.IfcGrossSideArea = nobj.IfcImportedProperties['GrossSideArea']
  if 'NominalWidth' in nobj.IfcImportedProperties:
    nobj.addProperty("App::PropertyString","IfcNominalWidth","IfcElementQuantity","string of imported NominalWidth (if available)")
    nobj.IfcNominalWidth = nobj.IfcImportedProperties['NominalWidth']
  if 'Width' in nobj.IfcImportedProperties:
    nobj.addProperty("App::PropertyString","IfcWidth","IfcElementQuantity","string of imported Width (if available)")
    nobj.IfcWidth = nobj.IfcImportedProperties['Width']
  
  return(nobj)


def setView(): 
  import FreeCADGui
  FreeCADGui.SendMsgToActiveView("ViewFit")
  FreeCADGui.activeDocument().activeView().viewAxometric()
  FreeCADGui.activeDocument().activeView().setCameraType("Perspective")


########################################################################################################################
########################################################################################################################
# Aufpassen, ArchObjekte haben ein VO und die Shape des ArchObjektes hat ein VO
# immer nur das VO des Arch Objektes aendern
# Wenn alle shape eingeschaltet werden liegen die beiden VO uebereinander !!!
#    if '_FreeCAD_shape_body' not in o.Name:    # es waere cooler ein eigenes PythonFeature


def colorPropertyMaterial():
  """
 Farben nach Property Material setzen
  
  """
  for o in FreeCAD.ActiveDocument.Objects:
    if '_FreeCAD_shape_body' not in o.Name:    # es waere cooler ein eigenes PythonFeature
      if hasattr(o,'Shape'):         
        if hasattr(o,'IfcImportedProperties'):
          if 'Material' in o.IfcImportedProperties:
            o.ViewObject.Transparency = 50
            if o.IfcImportedProperties['Material'] == 'Backstein':
              o.ViewObject.ShapeColor = (1.0,0.0,0.0)
            elif o.IfcImportedProperties['Material'] == 'Beton':
              o.ViewObject.ShapeColor = (0.0,1.0,0.0)
            else:
              o.ViewObject.ShapeColor = (1.0,1.0,1.0)
              o.ViewObject.Transparency = 0
        else:
          # make all shapes which have no IfcImportedProperties transparent.
          o.ViewObject.Transparency = 80
          print ("  Object " + o.Name + " has no IfcImportedProperties")


  
# Problem, wass wenn IFCSLAB oder ifcslab oder codierung ???
def colorObjectMaterial():
  """ Farben nach Objekt Material setzen
  
  """
  print "CedrusColours"
  for o in FreeCAD.ActiveDocument.Objects:
    if '_FreeCAD_shape_body' not in o.Name:    # es waere cooler ein eigenes PythonFeature
      if hasattr(o,'Shape'):         
        o.ViewObject.Visibility = True 
        if hasattr(o,'IfcObjectType') and hasattr(o,'IfcMaterial'):
          if   (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and (o.IfcMaterial == 'Ortbeton' or o.IfcMaterial == 'Beton'):
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (0.0,1.0,0.0)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Backstein':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,0.22,0.22)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Monobrick':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,0.22,0.22)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Kalksandstein':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (0.624,0.0,0.0)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Leichtbau':
            o.ViewObject.Transparency = 30              
            o.ViewObject.ShapeColor = (0.98,0.647,0.275)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Elementbeton':
            o.ViewObject.Transparency = 20              
            o.ViewObject.ShapeColor = (0.659,0.659,1.0)
          elif (o.IfcObjectType  == 'IfcWallStandardCase' or o.IfcObjectType  == 'IfcWall') and o.IfcMaterial == 'Recyclingbeton':
            o.ViewObject.Transparency = 30             
            o.ViewObject.ShapeColor = (0.3,1.0,0.0)
          elif o.IfcObjectType  == 'IfcSlab' and (o.IfcMaterial == 'Ortbeton' or o.IfcMaterial == 'Beton'):
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,1.0,0.11)
          elif o.IfcObjectType  == 'IfcSlab' and o.IfcMaterial == 'Elementbeton':
            o.ViewObject.Transparency = 30              
            o.ViewObject.ShapeColor = (0.0,1.0,1.0)
          elif o.IfcObjectType  == 'IfcSlab' and o.IfcMaterial == 'Holz':
            o.ViewObject.Transparency = 30              
            o.ViewObject.ShapeColor = (0.98,0.647,0.275)
          elif o.IfcObjectType  == 'IfcSlab' and o.IfcMaterial == ' ':    # Dachhaut (Auenstein, Joho), steht auch im IfcSlab als Roof drin ToDo: auslesen
            o.ViewObject.Transparency = 60              
            o.ViewObject.ShapeColor = (1.0,0.667,0.941)
          elif o.IfcObjectType  == 'IfcRoof' and o.IfcMaterial == ' ':
            o.ViewObject.Transparency = 60
            o.ViewObject.ShapeColor = (1.0,0.667,0.941)
          elif o.IfcObjectType  == 'IfcFooting' and (o.IfcMaterial == 'Ortbeton' or o.IfcMaterial == 'Beton'):
            o.ViewObject.Transparency = 40
            o.ViewObject.ShapeColor = (0.51,0.314,0.157)
          elif o.IfcObjectType  == 'IfcFooting' and o.IfcMaterial == 'Magerbeton':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,0.5,0.0)
          elif o.IfcObjectType  == 'IfcBuildingElementProxy' and o.IfcMaterial == 'Magerbeton':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,0.5,0.0)
          elif o.IfcObjectType  == 'IfcColumn' and (o.IfcMaterial == 'Ortbeton' or o.IfcMaterial == 'Beton'):
            o.ViewObject.Transparency = 0
            o.ViewObject.ShapeColor = (0.0,0.431,0.0)
          elif o.IfcObjectType  == 'IfcColumn' and o.IfcMaterial == 'Elementbeton':
            o.ViewObject.Transparency = 0
            o.ViewObject.ShapeColor = (0.0,1.0,1.0)
          elif o.IfcObjectType  == 'IfcColumn' and o.IfcMaterial == 'Baustahl':
            o.ViewObject.Transparency = 0
            o.ViewObject.ShapeColor = (0.0,0.0,1.0)
          elif o.IfcObjectType  == 'IfcColumn' and o.IfcMaterial == 'Holzbau':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (0.98,0.647,0.275)
          elif o.IfcObjectType  == 'IfcBeam' and (o.IfcMaterial == 'Ortbeton' or o.IfcMaterial == 'Beton'):
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (0.0,0.431,0.0)
          elif o.IfcObjectType  == 'IfcBeam' and o.IfcMaterial == 'Fugenmaterial':
            o.ViewObject.Transparency = 30
            o.ViewObject.ShapeColor = (1.0,0.0,1.0)

          
          else:
            o.ViewObject.ShapeColor = (1.0,1.0,1.0)  # weiss sieht schoen cremig aus :-)
            o.ViewObject.Transparency = 0
            print (o.Name + ' --> ' + o.IfcObjectType + ' --> ' + o.IfcMaterial)
        else:
          # make all shapes which have no IfcObjectType transparent.
          o.ViewObject.Transparency = 0
          o.ViewObject.ShapeColor = (0.0,0.0,0.0)
          print ("  Object " + o.Name + " has no IfcObjectType or no IfcMaterial")



def getObjectMaterialList():
  """ Liste aller Objekt Materialien
  
  """
  objectmateriallist = []
  for o in FreeCAD.ActiveDocument.Objects:
    if '_FreeCAD_shape_body' not in o.Name:    # es waere cooler ein eigenes PythonFeature
      if hasattr(o,'Shape'):         
        if hasattr(o,'IfcImportedMaterials'):
          for k in o.IfcImportedMaterials:
            if k not in objectmateriallist:
              print k
              objectmateriallist.append(k)
        else:
          print ("  Object " + o.Name + " has no IfcImportedMaterials")



def farbImport():
  """
  Falls Farben in den propertysets definiert sind. Aeltere ifc-dateien
  
  """
  for o in FreeCAD.ActiveDocument.Objects:
    if '_FreeCAD_shape_body' not in o.Name:    # es waere cooler ein eigenes PythonFeature
      if hasattr(o,'Shape'):         
        if hasattr(o,'IfcImportedProperties'):
          if 'Blue' in o.IfcImportedProperties:
            print o.Name
            print ( o.Name + '   R: ' + o.IfcImportedProperties['Red'] + '   G: ' +  o.IfcImportedProperties['Green'] + '   B: ' +  o.IfcImportedProperties['Blue'] )
            r = int(o.IfcImportedProperties['Red'])/255.0
            #print r
            g = int(o.IfcImportedProperties['Green'])/255.0
            b = int(o.IfcImportedProperties['Blue'])/255.0
            if int(o.IfcImportedProperties['Red']) == 229 and int(o.IfcImportedProperties['Green']) == 229 and int(o.IfcImportedProperties['Blue']) == 229 :
              print ('Mache Grau heller!')
              r = .999
              g = .999
              b = .999
            o.ViewObject.ShapeColor = (r,g,b)
            o.ViewObject.Transparency = 0
        else:
          # make all shapes which have no IfcImportedProperties transparent too.
          o.ViewObject.Transparency = 75
          print ("  Object " + o.Name + " has no IfcImportedProperties")



def eineFarbe():
  for o in FreeCAD.ActiveDocument.Objects:
    if '_FreeCAD_shape_body' not in o.Name:    # nur die PythonFeatures. Es waere cooler ein eigenes PythonFeature
      if hasattr(o,'Shape'):      
        o.ViewObject.ShapeColor = (0.3,0.4,0.4)   
        o.ViewObject.Transparency = 0
        o.ViewObject.Visibility = True 




def volumeTest():
  print "VolumeTest"
  for o in FreeCAD.ActiveDocument.Objects:
    if hasattr(o,'Shape'):         
      o.ViewObject.ShapeColor = (0.0,0.0,1.0)   # all shapes blue and transparent
      o.ViewObject.Transparency = 75
      o.ViewObject.Visibility = False 
      if '_FreeCAD_shape_body' not in o.Name:    # nur die PythonFeatures. Es waere cooler ein eigenes PythonFeature
        o.ViewObject.Visibility = True 
        try:
          volumeFreeCAD = o.Shape.Volume  # wenn shape kein solid ist wird eine exception ausgeloest. diese fangen wir ab!!!
        except:
          print ("  error calculating volume of " + o.Name + " Shape seams invalid")
          o.ViewObject.ShapeColor = (1.0,1.0,0.0)   # yellow if invalid shape
          o.ViewObject.Transparency = 0
        if hasattr(o,'IfcImportedProperties'):
          volumeImported = 0 
          if 'NetVolume' in o.IfcImportedProperties:
            volumeImported = float(o.IfcImportedProperties['NetVolume'])
            #volumeFreeCAD = volumeFreeCAD*1E-9         # Allplan    
          elif 'Volume' in o.IfcImportedProperties:  
            volumeImported = float(o.IfcImportedProperties['Volume'])
          if volumeImported != 0:
            o.ViewObject.ShapeColor = (0.3,0.4,0.4)   # grau wenn IfcImportedProperties vorhanden sind 
            o.ViewObject.Transparency = 0             # undurchsichtig
            #print o.Name
            #print o.Shape.Volume*1E-9
            q = volumeFreeCAD / volumeImported   
            #if q < 0.990 or q > 1.010:
            if q < 0.90 or q > 1.10:
              o.ViewObject.ShapeColor = (1.0,0.0,0.0)     # rot wenn volumen nicht uebereinstimmt
              print ("  Object: " + o.Name  + " --> Volumes not equal: volumeFreeCAD / volumeImported = " + str(q))
            else:
              #print ("  Object: " + o.Name  + " --> Volumes equal: volumeFreeCAD / volumeImported = " + str(q))
              o.ViewObject.Transparency = 80  #grau ist es schon nun auch durchsichtig wenn volumen stimmt
        else:
          print ('  Object ' + o.Name + ' ' + o.IfcObjectType + ' ' + ' has no IfcImportedProperties')
          o.ViewObject.ShapeColor = (0.0,1.0,0.0)   #green if no IfcImportedProperties available
          #o.ViewObject.Transparency = 0
          o.ViewObject.Visibility = False

'''
def volumetest():
  sys.path.append('/home/hugo/Documents/projekte--ifc/freecad/python--freecad--ArchToolBox/')
  import ArchToolBox as ATB
  ATB.importtest_volumequantity()
'''


'''
 cd /home/hugo/Documents/projekte--ifc/freecad/development/snapshot/free-cad-code/build/bin/
 ./FreeCAD 
 ./FreeCAD ../../../../../BIM--IFC/modelle--oeffentlich/Eckfenster--001.ifc 
 ./FreeCAD ../../../../../BIM--IFC/modelle--bhb--kleine--oBew/calmo.ifc
'''
'''
reload(importIFC)
'''



