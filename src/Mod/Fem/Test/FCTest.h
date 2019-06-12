#include "FCConfig.h"
#include <gtest/gtest.h>
#include <App/Document.h>


void saveAndLoad(App::Document** doc);

class DocumentTest : public ::testing::Test {
    protected:
        void SetUp() override;
        void TearDown() override;
        App::Document* doc;
};
