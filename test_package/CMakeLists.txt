project(PackageTest C)
cmake_minimum_required(VERSION 2.8)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(testPackage test.c)
include_directories(${CMAKE_CURRENT_SOURCE_DIR} ${CONAN_INCLUDE_DIRS})
target_link_libraries(testPackage ${CONAN_LIBS})