#define AppFemExport
#define PartExport

#include <iostream>
#include "FCConfig.h"
#include <gtest/gtest.h>
#include <Test/FCTest.h>
#include <App/ComplexGeoData.h>
#include <App/DocumentObject.h>
#include <Mod/Part/App/TopoShape.h>
#include <Mod/Part/App/FeaturePartBox.h>
#include <Mod/Fem/App/FemConstraint.h>
#include <BRepGProp_Face.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS.hxx>

class ConstraintBase :public DocumentTest {};

TEST_F(ConstraintBase, OneFaceNormal)
{
    auto& constraint = ADD_OBJECT(Fem::Constraint);
    auto& box = ADD_OBJECT(Part::Box);
    constraint.References.setValue(&box, "Face1");
    doc->recompute();
    Base::Vector3d normal {constraint.NormalDirection.getValue()};
    ASSERT_EQ(constraint.References.getSize(), 1);
    ASSERT_EQ(normal, Base::Vector3d(-1, 0, 0));
}

TEST_F(ConstraintBase, MultipleFacesNormal)
{
    auto& constraint = ADD_OBJECT(Fem::Constraint);
    auto& box = ADD_OBJECT(Part::Box);
    std::vector<App::DocumentObject*> objs {&box, &box, &box};
    std::vector<std::string> subs {"Face1", "Face4", "Face2"};
    constraint.References.setValues(objs, subs);
    doc->recompute();
    Base::Vector3d normal {constraint.NormalDirection.getValue()};
    ASSERT_EQ(constraint.References.getSize(), 3);
    ASSERT_EQ(normal, Base::Vector3d(-1, 0, 0));
}

TEST_F(ConstraintBase, EmptyNormal)
{
    auto& constraint = ADD_OBJECT(Fem::Constraint);
    doc->recompute();
    Base::Vector3d normal {constraint.NormalDirection.getValue()};
    ASSERT_EQ(normal, Base::Vector3d(0, 0, 1));
}

TEST_F(ConstraintBase, CurvedFaceNormal)
{
    auto& constraint = ADD_OBJECT(Fem::Constraint);
    auto& cylinder = ADD_OBJECT(Part::Box);
    constraint.References.setValue(&cylinder, "Face1");
    doc->recompute();
    Base::Vector3d normal {constraint.NormalDirection.getValue()};
    ASSERT_EQ(normal, Base::Vector3d(-1, 0, 0));
}
