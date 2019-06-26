#include "FCConfig.h"
#include <gtest/gtest.h>

#include <Base/Interpreter.h>
#include <Base/Exception.h>
#include <Base/Vector3D.h>
#include <App/Document.h>

#include <gp_Vec.hxx>

/**
 * @brief Calls DocumentTest::addObject with matching arguments.
 *
 * @details
 *  FreeCADs typesystem is based on strings while the native C++ typesystem
 *  uses template arguments. Those two can't communicate which forces
 *  DocumentTest::addObject to require the typename as a string (for FreeCAD)
 *  and as a template argument (for casting). This macro only requires the type
 *  argument once and calls DocumentTest::addObject with that argument used
 *  twice.
 *
 *  This macro should be used in most cases instead of calling
 *  DocumentTest::addObject directly because it's less error prone. For info
 *  about the return value and exceptions see DocumentTest::addObject.
 */
#define ADD_OBJECT(t) addObject<t>(#t)


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
         * @brief Add Document Object to test document.
         *
         * @details
         *  Adds the Document Object specified by the type to the document used
         *  by this test. It than casts the Object to the type given by the
         *  template paramter @p T before returning a reference to it.
         *
         * @tparam T
         *  Convert the @ref DocumentObject to this type before returning a
         *  reference to it. It must be possible to cast the object of the type
         *  given by @p type to a object of type @p T.
         * @param type
         *  The type string used to call addObject of @ref Document. The type
         *  must be a child class of @ref DocumentObject and initialized
         *  properly.
         *
         * @return
         *  A reference to the just added Document Object. Before it is
         *  returned it is cast to the type given by the template parameter T.
         *
         * @throw Base::TypeError
         *  Is thrown when the type specified by the argument @p type can't be
         *  cast to @p T, @p type doesn't exist or if @p type isn't a child of
         *  @ref DocumentObject. Those errors can be distinguished by the
         *  message of the exception.
         */
        template <typename T>
        T& addObject(std::string type);

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

template <typename T>
T& DocumentTest::addObject(std::string type)
{
    T* obj;
    try {
        obj = dynamic_cast<T*>(doc->addObject(type.c_str()));
    } catch (Base::PyException& e) {
        throw Base::TypeError("type does not exist");
    }
    if (obj == nullptr)
        throw Base::TypeError("incompatible cast");
    return *obj;
}
