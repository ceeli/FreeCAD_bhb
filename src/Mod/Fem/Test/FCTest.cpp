#include "FCTest.h"
#include <boost/filesystem.hpp>

#include <App/Application.h>
#include <Base/Vector3D.h>
#include <App/Document.h>

#include <gp_Vec.hxx>

void DocumentTest::SetUp()
{
    doc = App::GetApplication().newDocument();
}

void DocumentTest::TearDown()
{
    App::GetApplication().closeDocument(doc->getName());
}

void DocumentTest::saveAndLoad()
{
    auto path = boost::filesystem::temp_directory_path();
    path /= boost::filesystem::unique_path();
    doc->saveAs(path.c_str());
    App::GetApplication().closeDocument(doc->getName());
    doc = App::GetApplication().openDocument(path.c_str());
}

bool operator==(Base::Vector3d fc, gp_Vec oc)
{
    Base::Vector3d ocConv {oc.X(), oc.Y(), oc.Z()};
    return fc == ocConv;
}

bool operator==(gp_Vec oc, Base::Vector3d fc)
{
    return fc == oc;
}

bool operator!=(Base::Vector3d fc, gp_Vec oc)
{
    return !(fc == oc);
}

bool operator!=(gp_Vec oc, Base::Vector3d fc)
{
    return !(fc == oc);
}

std::ostream& operator<<(std::ostream& stream, Base::Vector3d const& vec)
{
    return stream << "Base::Vector3d(" << vec.x << ", " << vec.y << ", " << vec.z << ")";
}
