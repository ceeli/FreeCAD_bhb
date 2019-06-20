#define AppFemExport

#include "FCConfig.h"
#include "FCTest.h"

#include <gtest/gtest.h>

#include <App/Application.h>
#include <App/Document.h>
#include <App/FeatureTest.h>


class FCTest :public DocumentTest {};


TEST_F(FCTest, notNull)
{
    ASSERT_NE(doc, nullptr);
}

TEST_F(FCTest, isNewDoc1)
{
    const std::string message = "Hello, World!";
    ASSERT_TRUE(doc->Comment.isEmpty());
    doc->Comment.setValue(message);
}

TEST_F(FCTest, isNewDoc2)
{
    const std::string message = "Hello, World!";
    ASSERT_TRUE(doc->Comment.isEmpty());
    doc->Comment.setValue(message);
}

TEST_F(FCTest, saveAndLoad)
{
    App::FeatureTest* obj;
    std::string name {"object"};
    doc->addObject("App::FeatureTest", name.c_str());

    obj = static_cast<App::FeatureTest*>(doc->getObject(name.c_str()));
    const int normSaved = obj->Integer.getValue() + 1;
    const int tranSaved = obj->TypeTransient.getValue() + 1;
    obj->Integer.setValue(normSaved);
    obj->TypeTransient.setValue(tranSaved);

    saveAndLoad();

    obj = static_cast<App::FeatureTest*>(doc->getObject(name.c_str()));
    ASSERT_EQ(obj->Integer.getValue(), normSaved);
    ASSERT_NE(obj->TypeTransient.getValue(), tranSaved);
}
