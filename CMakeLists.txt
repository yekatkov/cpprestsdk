cmake_minimum_required(VERSION 3.1)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

project(cpprestsdk-root NONE)
enable_testing()
add_subdirectory(Release)
