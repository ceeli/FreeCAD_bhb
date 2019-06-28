add_subdirectory(${PROJECT_SOURCE_DIR}/src/3rdParty/googletest src/3rdParty/googletest)

include_directories(
    ${PYTHON_INCLUDE_DIRS}
)

add_executable(
    FreeCADTest
    FreeCADTest.cpp
    TestAnalysis.cpp
    TestFCTest.cpp
    TestConstraint.cpp
    FCTest.cpp
)

target_link_libraries(
    FreeCADTest
    FreeCADApp
    Fem
    Part
    gtest
    ${Qt5Core_LIBRARIES}
    ${Qt5Xml_LIBRARIES}
    #${Python_LIBRARIES}
)

include_directories(
    ${OCC_INCLUDE_DIR}
)

SET_BIN_DIR(FreeCADTest FreeCADTest)

install (
    TARGETS FreeCADTest
    RUNTIME DESTINATION bin
)
