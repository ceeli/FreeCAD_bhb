#include "FCTest.h"
#include <boost/filesystem.hpp>
#include <App/Application.h>
#include <App/Document.h>

void saveAndLoad(App::Document**)
{
}

void DocumentTest::SetUp()
{
    doc = App::GetApplication().newDocument();
}

void DocumentTest::TearDown()
{
    App::GetApplication().closeDocument(doc->getName());
}
