enable_testing()

find_package(Catch2 CONFIG REQUIRED)

# Collect all unit test source files
set(UNIT_TEST_SOURCES
    main.cpp
    unit/test_curves.cpp
    unit/test_white_balance.cpp
)

add_executable(unit_tests
    ${UNIT_TEST_SOURCES}
)

target_link_libraries(unit_tests
    PRIVATE
    Catch2::Catch2
    Catch2::Catch2WithMain
    filmulator-lib
)

# Discover tests for CTest integration
include(Catch)
catch_discover_tests(unit_tests)
