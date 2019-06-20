#include "FCTest.h"
#include <boost/filesystem.hpp>
#include <App/Application.h>
#include <App/Document.h>

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
