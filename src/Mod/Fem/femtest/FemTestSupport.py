import unittest
import os.path

import FreeCAD
import femsolver.run
from femtools import femutils
import AppTestSupport


class TestSetupError(Exception):
    pass


class SolverTest(AppTestSupport.BaseTest):

    TEST_DIR = os.path.join(
        FreeCAD.getHomePath(),
        "Mod/Fem/femtest/testfiles/problems")
    EXTENSION = ".FCStd"

    def setUp(self):
        self.doc = None
        self.solver = None
        self.pipe = None

    def tearDown(self):
        if self.doc is not None:
            FreeCAD.closeDocument(self.doc.Name)

    def addMember(self, proxy):
        if self.doc is None:
            raise TestSetupError("no document loaded")
        analyses = self.doc.findObjects("Fem::FemAnalysis")
        if len(analyses) == 0:
            raise TestSetupError("no Analysis found")
        if len(analyses) > 1:
            raise TestSetupError("multiple Analyses found")
        member = femutils.createObject(self.doc, "", proxy)
        analyses[0].addObject(member)
        return member

    def addSolver(self, proxy):
        self.solver = self.addMember(proxy)

    def addEquation(self, eqId):
        if self.doc is None:
            raise TestSetupError("no document loaded")
        if self.solver is None:
            raise TestSetupError("no solver found")
        self.solver.Proxy.addEquation(self.solver, eqId)


    def loadSimulation(self, name):
        file_name = name + self.EXTENSION
        path = os.path.join(self.TEST_DIR, file_name)
        self.doc = FreeCAD.open(path)

    def runSimulation(self):
        self.doc.recompute()
        femsolver.run.run_fem_solver(self.solver)
        self._convertResults()
        self._loadResults()

    def assertDataAtPoint(self, name, point, expect, rel_tol=1e-3, abs_tol=0.0):
        dataAtPoint = self.doc.addObject(
            "Fem::FemPostDataAtPointFilter")
        self._addFilter(dataAtPoint)
        self.doc.recompute()
        dataAtPoint.FieldName = name
        self.doc.recompute()
        dataAtPoint.Center = point
        self.doc.recompute()
        dataAtPoint.FieldName = name
        dataAtPoint.Center = FreeCAD.Vector(point)
        values = dataAtPoint.PointData
        if not all(self._isclose(x, expect, rel_tol, abs_tol) for x in values):
            self.doc.removeObject(dataAtPoint.Name)
            msg = "{} not close enough to {}".format(values, expect)
            raise AssertionError(msg)
        self.doc.removeObject(dataAtPoint.Name)

    def _loadResults(self):
        self.pipe = None
        pipelines = self.doc.findObjects("Fem::FemPostPipeline")
        if len(pipelines) == 0:
            raise TestSetupError("no Result found")
        if len(pipelines) > 1:
            raise TestSetupError("multiple Results found")
        self.pipe = pipelines[0]

    def _convertResults(self):
        results = self.doc.findObjects("Fem::FemResultObject")
        for r in results:
            obj = self.doc.addObject("Fem::FemPostPipeline")
            obj.load(r)

    def _isclose(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def _addFilter(self, f):
        self.pipe.Filter += [f]
