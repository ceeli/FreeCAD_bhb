add_library(FemTest OBJECT
    TestAnalysis.cpp
    TestFCTest.cpp
    TestConstraint.cpp
)

target_link_libraries(FemTest
    PUBLIC
        gtest
    PRIVATE
        TestLib
        Part
        Fem
)

target_include_directories(FemTest
    PRIVATE
        ${PYTHON_INCLUDE_DIRS}
        ${OCC_INCLUDE_DIR}
)
