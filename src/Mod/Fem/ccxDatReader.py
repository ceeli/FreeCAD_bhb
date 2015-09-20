#***************************************************************************
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Author: Przemo Firszt <przemo@firszt.eu>                              *
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
import os

if open.__module__ == '__builtin__':
    pyopen = open  # because we'll redefine open below

EIGENVALUE_OUTPUT_SECTION = "     E I G E N V A L U E   O U T P U T"
#PARTICIPATION_FACTORS_SECTION = "     P A R T I C I P A T I O N   F A C T O R S"
#EFFECTIVE_MODAL_MASS_SECTION = "     E F F E C T I V E   M O D A L   M A S S"
#TOTAL_EFFECTIVE_MASS_SECTION = "     T O T A L   E F F E C T I V E   M A S S"
DISPLACEMENT_OUTPUT_SECTION = ' displacements (vx,vy,vz) for set '
STRESS_OUTPUT_SECTION = ' stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set '

# read a calculix result file and extract the data
def readResult(dat_input):
    dat_file = pyopen(dat_input, "r")
    eigenvalue_output_section_found = False
    displacement_output_section_found = False
    stess_output_section_found = False
    reading_section = False
    eigenmodes = []
    node_displacements = {}
    results = {}

    for line in dat_file:
        if EIGENVALUE_OUTPUT_SECTION in line:
            eigenvalue_output_section_found = True
            #print ("Found EIGENVALUE_OUTPUT_SECTION")
        if eigenvalue_output_section_found:
            #print line
            try:
                mode = int(line[0:7])
                #print ("Found mode {}".format(mode))
                mode_frequency = float(line[39:55])
                #print ("Found mode frequency {}".format(mode_frequency))
                m = {}
                m['eigenmode'] = mode
                m['frequency'] = mode_frequency
                eigenmodes.append(m)
                reading_section = True
            except:
                if reading_section:
                    #print ("Conversion error after reading section started, so it's the end of section")
                    eigenvalue_output_section_found = False
                    reading_section = False
        if DISPLACEMENT_OUTPUT_SECTION in line:
            displacement_output_section_found = True
            # print ("Found DISPLACEMENT_OUTPUT_SECTION")
        if displacement_output_section_found:
            # print line
            try:
                nodeID = int(line[0:10])
                disp_x = float(line[12:24])
                disp_y = float(line[26:38])
                disp_z = float(line[40:52])
                node_displacements[nodeID] = [disp_x, disp_y, disp_z]
                reading_section = True
            except:
                if reading_section:
                    print ("Conversion error after reading_section started, so it's the end of section")
                    displacement_output_section_found = False
                    reading_section = False
        '''
        if STRESS_OUTPUT_SECTION in line:
            stress_output_section_found = True
            # print ("Found STRESS_OUTPUT_SECTION")
        if displacement_output_section_found:
            # print line
            try:
                pass
            except:
                if reading_section:
                    print ("Conversion error after mode reading started, so it's the end of section")
                    displacement_output_section_found = False
                    reading_section = False
        '''
    dat_file.close()
    results['eigenmodes'] = eigenmodes
    results['node_displacements'] = node_displacements
    return results


def import_dat(filename, Analysis=None):
    r = readResult(filename)
    print ("Results {}".format(r))


def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc

    import_dat(filename)


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)

'''
import ccxDatReader
ccxDatReader.import_dat('/home/hugo/Desktop/CalculiX--Results/Plane_Mesh.dat')
#ccxDatReader.import_dat('/home/hugo/Desktop/CalculiX--Results/Mesh.dat')
'''