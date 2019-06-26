#include "FCConfig.h"
#include <gtest/gtest.h>

#include <Base/Vector3D.h>
#include <App/Document.h>

#include <gp_Vec.hxx>


/**
 * @brief Fixture offering an App::Document and related testing utilities.
 *
 * @details
 *  This GTest Fixture manages the lifetime of an App::Document. A new
 *  App::Document is created for each test and closed automatically afterwards.
 *  Tests using this Fixture can just use the protected #doc member to execute
 *  tests. Test should not close #doc or open additional documents. #doc is
 *  garanteed to hold a valid pointer to a App::Document. No checks for nullptr
 *  should be used.
 *
 *  In addition the Fixture provides a few utility methods useful for testing
 *  App::DocumentObject. All protected methods in this class except SetUp() and
 *  TearDown() are utility methods designed to help with test case creation. See
 *  the documentation of the individual methods for more info.
 */
class DocumentTest : public ::testing::Test {
    protected:
        void SetUp() override;
        void TearDown() override;

        /**
         * @brief Save, close and load the test document.
         *
         * @details
         *  Saves the doc member to a temporary file, closes the document and
         *  than opens it and assings it to the doc member. This method is
         *  useful to test if your App::DocumentObject behaves they way it
         *  should when it is saved and loaded by the user.
         */
        void saveAndLoad();

        /**
         * @brief App::Document pointer managed by this Fixture.
         *
         * @details
         *  This App::Document pointer is managed automatically by the Fixture
         *  A new App::Document is created for each test and closed
         *  automatically afterwards. The pointer is garanteed to hold a valid
         *  reference to a App::Document. No checks for nullptr should be used.
         */
        App::Document* doc;
};

bool operator==(Base::Vector3d fc, gp_Vec oc);
bool operator!=(Base::Vector3d fc, gp_Vec oc);
bool operator==(gp_Vec oc, Base::Vector3d fc);
bool operator!=(gp_Vec oc, Base::Vector3d fc);
std::ostream& operator<<(std::ostream& stream, Base::Vector3d const& vec);
