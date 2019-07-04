#define AppFemExport

#include "FCConfig.h"
#include <Test/FCTest.h>

#include <gtest/gtest.h>

#include <Base/Exception.h>
#include <Base/Vector3D.h>
#include <App/DocumentObjectGroup.h>
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

TEST_F(FCTest, addObjectMacro)
{
    (void)ADD_OBJECT(App::FeatureTest);
    ASSERT_EQ(doc->countObjectsOfType(App::FeatureTest::getClassTypeId()), 1);
}

TEST_F(FCTest, addObjectValid)
{
    (void)addObject<App::FeatureTest>("App::FeatureTest");
    ASSERT_EQ(doc->countObjectsOfType(App::FeatureTest::getClassTypeId()), 1);
}

TEST_F(FCTest, addObjectIncompatible)
{
    ASSERT_THROW(
        addObject<App::DocumentObjectGroup>("App::FeatureTest"),
        Base::TypeError);
}

TEST_F(FCTest, addObjectNotDocument1)
{
    ASSERT_THROW(
        addObject<Base::Vector3d>("Base::Vector3d"),
        Base::TypeError);
}

TEST_F(FCTest, addObjectNotDocument2)
{
    ASSERT_THROW(
        addObject<App::FeatureTest>("Base::Vector3d"),
        Base::TypeError);
}

TEST_F(FCTest, addObjectNonExistent)
{
    ASSERT_THROW(
        addObject<App::FeatureTest>("Ap::Typo"),
        Base::TypeError);
}
