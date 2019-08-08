import unittest

import FreeCAD
from . import support_solver
import femsolver.elmer.solver
import femsolver.calculix.solver


class TestCantileverEndLoad(support_solver.SolverTest):
    """ Simulation of Cantilever with End Load

    A beam that is fixed on one side and has a downwards load applied to it on
    the opposite side. No other forces (like gravity) are considered. The
    dimensions (LxWxH) of the beam are 10x3x2 mm. A force of 100 N is appied on
    the end of the beam that is not fixed. The displacement can be calculated
    with the following formular: d = (F*x^2)/(6*E*I) * (3*L-x) where E is the
    elastic modulus of the material and I = (w*h^3)/12 where w and h are the
    width and height of the beam.

    E = 210,000 MPa / 1e3 (mm) = 0.21e9
    N = 100N * 1e3 (mm) = 0.1e6
    I = (3*2^3)/12 = 2

    d(0)                                               ~ 0.0000 mm
    d(2.5) = (0.1e6*2.5^2) / (6*0.21e9*2) * (3*10-2.5) ~ 0.0068 mm
    d(5)   = (0.1e6*5.0^2) / (6*0.21e9*2) * (3*10-5.0) ~ 0.0248 mm
    d(7.5) = (0.1e6*7.5^2) / (6*0.21e9*2) * (3*10-7.5) ~ 0.0502 mm
    d(10)  = (0.1e6* 10^2) / (6*0.21e9*2) * (3*10- 10) ~ 0.0793 mm
    """

    def setUp(self):
        self.loadSimulation("cantilever_end_load")

    def assertResult(self, variable, error):
        t = 0.0793 * error
        self.assertDataAtPoint(variable, (  0, 0, 0), 0.0000, abs_tol=t)
        self.assertDataAtPoint(variable, (2.5, 0, 0), 0.0068, abs_tol=t)
        self.assertDataAtPoint(variable, (  5, 0, 0), 0.0248, abs_tol=t)
        self.assertDataAtPoint(variable, (7.5, 0, 0), 0.0502, abs_tol=t)
        self.assertDataAtPoint(variable, ( 10, 0, 0), 0.0793, abs_tol=t)

    def testWithElmer(self):
        self.addSolver(femsolver.elmer.solver.Proxy)
        self.addEquation("Elasticity")
        self.runSimulation()
        self.assertResult("displacement", 0.03)

    def testWithCcx(self):
        self.addSolver(femsolver.calculix.solver.Proxy)
        self.runSimulation()
        self.assertResult("Displacement", 0.03)


class TestCantileverUniformLoad(support_solver.SolverTest):
    """ Simulation of Cantilever with End Load

    A beam that is fixed on one side and has a uniform load it on the top. No
    other forces (like gravity) are considered. The dimensions (LxWxH) of the
    beam are 10x3x2 mm. A force of 500 N is appied on the top surface of the
    beam pressind downwards. The displacement can be calculated with the
    following formular: d = (qx^2)/(24EI)*(6L^2 - 4Lx + x^2) where E is the
    elastic modulus of the material and I = (w*h^3)/12 where w and h are the
    width and height of the beam.

    E = 210,000 MPa / 1e3 (mm) = 0.21e9
    N = 500N * 1e3 (mm) = 0.5e6
    L = 10 mm
    q = N/L = 50,000
    I = (3*2^3)/12 = 2

    d(0)                                                                 ~ 0.0000 mm
    d(2.5) = (50000*2.5^2) / (24*0.21e9*2) * (6*10^2 - 4*10*2.5 + 2.5^2) ~ 0.0157 mm
    d(5)   = (50000*5.0^2) / (24*0.21e9*2) * (6*10^2 - 4*10*5.0 + 5.0^2) ~ 0.0527 mm
    d(7.5) = (50000*7.5^2) / (24*0.21e9*2) * (6*10^2 - 4*10*7.5 + 7.5^2) ~ 0.0994 mm
    d(10)  = (50000* 10^2) / (24*0.21e9*2) * (6*10^2 - 4*10* 10 +  10^2) ~ 0.1488 mm
    """

    def setUp(self):
        self.loadSimulation("cantilever_uniform_load")

    def assertResult(self, variable, error):
        t = 0.1488 * error
        self.assertDataAtPoint(variable, (  0, 0, 0), 0.0000, abs_tol=t)
        self.assertDataAtPoint(variable, (2.5, 0, 0), 0.0157, abs_tol=t)
        self.assertDataAtPoint(variable, (  5, 0, 0), 0.0527, abs_tol=t)
        self.assertDataAtPoint(variable, (7.5, 0, 0), 0.0994, abs_tol=t)
        self.assertDataAtPoint(variable, ( 10, 0, 0), 0.1488, abs_tol=t)

    def testWithElmer(self):
        self.addSolver(femsolver.elmer.solver.Proxy)
        self.addEquation("Elasticity")
        self.runSimulation()
        self.assertResult("displacement", 0.04)

    def testWithCcx(self):
        self.addSolver(femsolver.calculix.solver.Proxy)
        self.runSimulation()
        self.assertResult("Displacement", 0.04)
