find_package (Python COMPONENTS Interpreter Development)
include_directories("${Python_INCLUDE_DIRS}")

find_package(GTest REQUIRED)

add_executable(
    FreeCADTest
    FreeCADTest.cpp
    TestAnalysis.cpp
    TestFCTest.cpp
    FCTest.cpp
)

target_link_libraries(
    FreeCADTest
    FreeCADApp
    Fem
    GTest::GTest
    ${Qt5Core_LIBRARIES}
    ${Qt5Xml_LIBRARIES}
    ${Python_LIBRARIES}
)

SET_BIN_DIR(FreeCADTest FreeCADTest)

install (
    TARGETS FreeCADTest
    RUNTIME DESTINATION bin
)
