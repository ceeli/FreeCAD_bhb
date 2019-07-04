# Add internal google test source to the build. This exports two library
# targets gtest and gtest_main.
add_subdirectory(
    ${PROJECT_SOURCE_DIR}/src/3rdParty/googletest
    src/3rdParty/googletest)


#################
#  Test Runner  #
#################

set(TEST_SOURCES
    FemTest
)

add_executable(FreeCADTest
    FreeCADTest.cpp
)

target_link_libraries(FreeCADTest
    gtest
    FreeCADApp
    ${TEST_SOURCES}
    ${Qt5Core_LIBRARIES}
    ${Qt5Xml_LIBRARIES}
)

target_include_directories(FreeCADTest
    PUBLIC
        ${PYTHON_INCLUDE_DIRS}
        ${OCC_INCLUDE_DIR}
)

SET_BIN_DIR(FreeCADTest FreeCADTest)
install(
    TARGETS FreeCADTest
    RUNTIME DESTINATION bin
)


##################
#  Test Library  #
##################

add_library(TestLib STATIC
    FCTest.cpp
)

target_link_libraries(TestLib
    PUBLIC
        gtest
        FreeCADApp
        Part
)

target_include_directories(TestLib
    PUBLIC
        ${OCC_INCLUDE_DIR}
        ${PYTHON_INCLUDE_DIRS}
)
