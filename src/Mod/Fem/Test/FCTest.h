#include "FCConfig.h"
#include <gtest/gtest.h>
#include <App/Document.h>



class DocumentTest : public ::testing::Test {
    protected:
        void SetUp() override;
        void TearDown() override;

        void saveAndLoad();
        App::Document* doc;
};
