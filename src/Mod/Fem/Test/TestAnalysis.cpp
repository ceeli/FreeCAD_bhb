#define AppFemExport

#include <iostream>
#include "FCConfig.h"
#include <gtest/gtest.h>
#include <App/Application.h>
#include <App/Document.h>
#include <Mod/Fem/App/FemAnalysis.h>
#include <Base/Uuid.h>
#include "FCTest.h"


class AnalysisDocument :public DocumentTest {};

TEST_F(AnalysisDocument, UidIsUnique)
{
    Fem::FemAnalysis* a = static_cast<Fem::FemAnalysis*>(
        doc->addObject("Fem::FemAnalysis"));
    Fem::FemAnalysis* b = static_cast<Fem::FemAnalysis*>(
        doc->addObject("Fem::FemAnalysis"));
    ASSERT_NE(nullptr, a);
    ASSERT_NE(nullptr, b);
    std::string aId = a->Uid.getValueStr();
    std::string bId = b->Uid.getValueStr();
    ASSERT_NE(aId, "");
    ASSERT_NE(bId, "");
    ASSERT_NE(a->Uid.getValueStr(), b->Uid.getValueStr());
}

TEST_F(AnalysisDocument, UidPersistent)
{
    Fem::FemAnalysis* obj = static_cast<Fem::FemAnalysis*>(
        doc->addObject("Fem::FemAnalysis"));
    ASSERT_NE(nullptr, obj);
    std::string saved {obj->Uid.getValueStr()};
    saveAndLoad();
    std::string loaded {obj->Uid.getValueStr()};
    ASSERT_EQ(saved, loaded);
}
