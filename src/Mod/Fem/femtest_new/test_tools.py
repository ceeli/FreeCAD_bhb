import unittest
import Test.FCTest as FCTest

import ObjectsFem
import femtools.femutils as femutils
import femsolver.elmer.solver as solver


class TestCreateObject(FCTest.DocumentTest):

    def testSimpleCreateObject(self):
        femutils.createObject(
            self.doc, "Solver", solver.Proxy, solver.ViewProxy);
        self.assertIsNotNone(self.doc.getObject("Solver"))

    def testNameConflictOnCreation(self):
        femutils.createObject(
            self.doc, "Solver", solver.Proxy, solver.ViewProxy);
        self.assertEqual(len(self.doc.Objects), 1)
        femutils.createObject(
            self.doc, "Solver", solver.Proxy, solver.ViewProxy);
        self.assertEqual(len(self.doc.Objects), 2)

    def testAutomaticNameGeneration(self):
        femutils.createObject(
            self.doc, "", solver.Proxy, solver.ViewProxy);
        self.assertEqual(len(self.doc.Objects), 1)

    def testDocArgumentNone(self):
        with self.assertRaises(Exception) as cm:
            femutils.createObject(None, "", solver.Proxy, solver.ViewProxy);

    def testNameArgumentNone(self):
        with self.assertRaises(Exception) as cm:
            femutils.createObject(self.doc, None, solver.Proxy, solver.ViewProxy);

    def testProxyArgumentNone(self):
        with self.assertRaises(Exception) as cm:
            femutils.createObject(self.doc, "", None, solver.ViewProxy);

#    def testViewProxyArgumentNone(self):
#        with self.assertRaises(Exception) as cm:
#            femutils.createObject(self.doc, "", solver.Proxy, None);


class TestFindAnalysisOfMember(FCTest.DocumentTest):

    def testMemberInFirstAnalysis(self):
        a = self.doc.addObject("Fem::FemAnalysis")
        b = self.doc.addObject("Fem::FemAnalysis")
        c = self.doc.addObject("Fem::FemAnalysis")
        member = solver.create(self.doc)
        a.addObject(member)
        result = femutils.findAnalysisOfMember(member)
        self.assertEqual(a, result)

    def testMemberInLastAnalysis(self):
        a = self.doc.addObject("Fem::FemAnalysis")
        b = self.doc.addObject("Fem::FemAnalysis")
        c = self.doc.addObject("Fem::FemAnalysis")
        member = solver.create(self.doc)
        c.addObject(member)
        result = femutils.findAnalysisOfMember(member)
        self.assertEqual(c, result)

    def testMemberInOnlyAnalysis(self):
        a = self.doc.addObject("Fem::FemAnalysis")
        member = solver.create(self.doc)
        a.addObject(member)
        result = femutils.findAnalysisOfMember(member)
        self.assertEqual(a, result)

    def testMemberInNoAnalysis(self):
        a = self.doc.addObject("Fem::FemAnalysis")
        b = self.doc.addObject("Fem::FemAnalysis")
        c = self.doc.addObject("Fem::FemAnalysis")
        member = solver.create(self.doc)
        result = femutils.findAnalysisOfMember(member)
        self.assertIsNone(result)

    def testMemberInGroup(self):
        a = self.doc.addObject("App::DocumentObjectGroup")
        b = self.doc.addObject("Fem::FemAnalysis")
        c = self.doc.addObject("Fem::FemAnalysis")
        member = solver.create(self.doc)
        a.addObject(member)
        result = femutils.findAnalysisOfMember(member)
        self.assertIsNone(result)
        

class TestGetMember(FCTest.DocumentTest):

    def testEmptyAnalysis(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        result = femutils.get_member(analysis, "Fem::FemSolverObjectElmer")
        self.assertListEqual(result, [])

    def testFemTypesystem(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        a = ObjectsFem.makeSolverElmer(self.doc)
        b = ObjectsFem.makeSolverCalculix(self.doc)
        c = ObjectsFem.makeSolverElmer(self.doc)
        d = ObjectsFem.makeConstraintFixed(self.doc)
        e = self.doc.addObject("Fem::FemPostPipeline")
        analysis.addObjects([a, b, c, d, e])
        result = femutils.get_member(analysis, "Fem::FemSolverObjectElmer")
        self.assertSameElements(result, [a, c])

    def testFCTypesystem(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        a = ObjectsFem.makeSolverElmer(self.doc)
        b = ObjectsFem.makeSolverCalculix(self.doc)
        c = ObjectsFem.makeSolverElmer(self.doc)
        d = ObjectsFem.makeConstraintFixed(self.doc)
        e = self.doc.addObject("Fem::FemPostPipeline")
        analysis.addObjects([a, b, c, d, e])
        result = femutils.get_member(analysis, "Fem::FemPostPipeline")
        self.assertSameElements(result, [e])

    def testFCTypesystemWithInheritance(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        a = ObjectsFem.makeSolverElmer(self.doc)
        b = ObjectsFem.makeSolverCalculix(self.doc)
        c = ObjectsFem.makeSolverElmer(self.doc)
        d = ObjectsFem.makeConstraintFixed(self.doc)
        e = self.doc.addObject("Fem::FemPostPipeline")
        analysis.addObjects([a, b, c, d, e])
        result = femutils.get_member(analysis, "Fem::FemPostObject")
        self.assertSameElements(result, [e])

    def testWithMultipleAnalysisObjects(self):
        a = self.doc.addObject("Fem::FemAnalysis")
        b = self.doc.addObject("Fem::FemAnalysis")
        a.addObject(ObjectsFem.makeSolverElmer(self.doc))
        a.addObject(ObjectsFem.makeSolverElmer(self.doc))
        b.addObject(ObjectsFem.makeSolverElmer(self.doc))
        result = femutils.get_member(a, "Fem::FemSolverObjectElmer")
        self.assertEqual(len(result), 2)
        result = femutils.get_member(b, "Fem::FemSolverObjectElmer")
        self.assertEqual(len(result), 1)


class TestIsDerivedFrom(FCTest.DocumentTest):

    def testFemTypesystemObject(self):
        a = ObjectsFem.makeSolverElmer(self.doc)
        self.assertTrue(
            femutils.is_derived_from(a, "Fem::FemSolverObjectElmer"))
        self.assertTrue(
            femutils.is_derived_from(a, "Fem::FemSolverObjectPython"))
        self.assertTrue(
            femutils.is_derived_from(a, "App::DocumentObject"))
        self.assertFalse(
            femutils.is_derived_from(a, "Fem::FemSolverObjectCalculix"))
        self.assertFalse(
            femutils.is_derived_from(a, "Fem::Constraint"))

    def testFCTypesystemObject(self):
        a = self.doc.addObject("Fem::FemPostPipeline")
        self.assertTrue(
            femutils.is_derived_from(a, "Fem::FemPostPipeline"))
        self.assertTrue(
            femutils.is_derived_from(a, "Fem::FemPostObject"))
        self.assertTrue(
            femutils.is_derived_from(a, "App::DocumentObject"))
        self.assertFalse(
            femutils.is_derived_from(a, "Fem::FemSolverObjectCalculix"))
        self.assertFalse(
            femutils.is_derived_from(a, "Fem::Constraint"))

    def testInvalidTypes(self):
        a = ObjectsFem.makeSolverElmer(self.doc)
        self.assertFalse(
            femutils.is_derived_from(a, "MadeUp::MadeUp"))
        self.assertFalse(
            femutils.is_derived_from(a, "Junk"))


class TestGetSingleMember(FCTest.DocumentTest):

    def testWithNoMatch(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        self.assertIsNone(
            femutils.get_single_member(analysis, "Fem::FemSolverObjectElmer"))

    def testWithSingleMatch(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        obj = ObjectsFem.makeSolverElmer(self.doc)
        analysis.addObject(obj)
        result = femutils.get_single_member(
            analysis, "Fem::FemSolverObjectElmer")
        self.assertEqual(result, obj)

    def testWithMultipleMatches(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        a = ObjectsFem.makeSolverElmer(self.doc)
        b = ObjectsFem.makeSolverElmer(self.doc)
        analysis.addObject(a)
        analysis.addObject(ObjectsFem.makeSolverCalculix(self.doc))
        analysis.addObject(b)
        result = femutils.get_single_member(
            analysis, "Fem::FemSolverObjectElmer")
        self.assertTrue(result == a or result == b)


class TestGetSeveralMember(FCTest.DocumentTest):

    def testWithEmptyAnalysis(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        y = femutils.get_several_member(analysis, "Fem::FemSolverObjectElmer")
        self.assertEqual(y, [])

    def testWithoutMatch(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        analysis.addObject(ObjectsFem.makeSolverCalculix(self.doc))
        y = femutils.get_several_member(analysis, "Fem::FemSolverObjectElmer")
        self.assertEqual(y, [])

    def testVertexSubtype(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        cube = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        constraint = ObjectsFem.makeConstraintFixed(self.doc)
        constraint.References = [(cube, ("Vertex1", "Vertex2"))]
        analysis.addObject(constraint)
        y = femutils.get_several_member(analysis, "Fem::ConstraintFixed")
        self.assertEqual(len(y), 1)
        self.assertEqual(y[0]["Object"], constraint)
        self.assertEqual(y[0]["RefShapeType"], "Vertex")


class TestGetMeshToSolve(FCTest.DocumentTest):

    def testWithEmptyAnalysis(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        self.assertIsNone(femutils.get_mesh_to_solve(analysis)[0])

    def testWithoutMesh(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        analysis.addObject(ObjectsFem.makeSolverCalculix(self.doc))
        self.assertIsNone(femutils.get_mesh_to_solve(analysis)[0])
        
    def testMultipleMeshes(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        analysis.addObject(ObjectsFem.makeMeshGmsh(self.doc))
        analysis.addObject(ObjectsFem.makeMeshGmsh(self.doc))
        self.assertIsNone(femutils.get_mesh_to_solve(analysis)[0])

    def testSingleMesh(self):
        analysis = self.doc.addObject("Fem::FemAnalysis")
        mesh = ObjectsFem.makeMeshGmsh(self.doc)
        analysis.addObject(mesh)
        self.assertEqual(femutils.get_mesh_to_solve(analysis)[0], mesh)


class TestTypeOfObj(FCTest.DocumentTest):

    def testFemTypesystem(self):
        a = ObjectsFem.makeSolverElmer(self.doc)
        self.assertEqual(femutils.type_of_obj(a), "Fem::FemSolverObjectElmer")

    def testFCTypesystem(self):
        a = self.doc.addObject("Fem::FemPostPipeline")
        self.assertEqual(femutils.type_of_obj(a), "Fem::FemPostPipeline")


class TestIsOfType(FCTest.DocumentTest):

    def testFemTypesystem(self):
        a = ObjectsFem.makeSolverElmer(self.doc)
        self.assertTrue(femutils.is_of_type(a, "Fem::FemSolverObjectElmer"))

    def testFCTypesystem(self):
        a = self.doc.addObject("Fem::FemPostPipeline")
        self.assertTrue(femutils.is_of_type(a, "Fem::FemPostPipeline"))


class TestGetBoundBoxOfAllDocumentShapes(FCTest.DocumentTest):

    def testEmptyDocument(self):
        box = femutils.getBoundBoxOfAllDocumentShapes(self.doc)
        self.assertIsNone(box)

    def testSingleShape(self):
        obj = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        box = femutils.getBoundBoxOfAllDocumentShapes(self.doc)
        box.isInside(obj.Shape.BoundBox)

    def testMultipleShapes(self):
        a = self.doc.addObject("Part::Box","Box")
        b = self.doc.addObject("Part::Box","Box")
        c = self.doc.addObject("Part::Box","Box")
        b.Width = 20
        c.Height = 5
        self.doc.recompute()
        box = femutils.getBoundBoxOfAllDocumentShapes(self.doc)
        box.isInside(a.Shape.BoundBox)
        box.isInside(b.Shape.BoundBox)
        box.isInside(c.Shape.BoundBox)


class TestGetRefshapeType(FCTest.DocumentTest):

    def testVertexSubtype(self):
        cube = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        constraint = ObjectsFem.makeConstraintFixed(self.doc)
        constraint.References = [(cube, ("Vertex1", "Vertex2"))]
        y = femutils.get_refshape_type(constraint)
        self.assertEqual(y, "Vertex")

    def testEdgeSubtype(self):
        cube = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        constraint = ObjectsFem.makeConstraintFixed(self.doc)
        constraint.References = [(cube, ("Edge1", "Edge2"))]
        y = femutils.get_refshape_type(constraint)
        self.assertEqual(y, "Edge")

    def testFaceSubtype(self):
        cube = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        constraint = ObjectsFem.makeConstraintFixed(self.doc)
        constraint.References = [(cube, ("Face1", "Face2"))]
        y = femutils.get_refshape_type(constraint)
        self.assertEqual(y, "Face")

    def testSolidSubtype(self):
        cube = self.doc.addObject("Part::Box","Box")
        self.doc.recompute()
        constraint = ObjectsFem.makeMaterialSolid(self.doc)
        constraint.References = [(cube, ("Solid1",))]
        y = femutils.get_refshape_type(constraint)
        self.assertEqual(y, "Solid")


#class TestPydecode(unittest.TestCase):
#
#    def testConvertString(self):
#        str(femutils.pydecode("Hello, World!"))
