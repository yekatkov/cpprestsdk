if (NOT WINDOWS_STORE AND NOT WINDOWS_PHONE)
  add_executable(BingRequest bingrequest.cpp)
  target_link_libraries(BingRequest cpprest)

  include(Settings)
  unexport_symbols(BingRequest)
endif()
