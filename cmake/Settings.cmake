###########################################################################
# Target specific cmake settings (when the target has already been created).


# Unexport symbols in shared libs (new/delete) for Linux/Android targets.
function(unexport_symbols TARGET_NAME)
    get_target_property(TARGET_TYPE ${TARGET_NAME} TYPE)
    if(TARGET_TYPE STREQUAL "SHARED_LIBRARY")
		
		set(LINK_CMD_FILE link.txt)

		if(NOT CMAKE_GENERATOR STREQUAL "Unix Makefiles")
			message(FATAL_ERROR "Cmake generator must be 'Unix Makefiles'!")
		endif()
			
		# add_custom_command(TARGET ${TARGET_NAME} 
		# 	POST_BUILD
		# 	# Generate version script file
		# 	COMMAND python ${CMAKE_MODULE_PATH}/unexport.py
		# 	${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/lib${TARGET_NAME}.so ${CMAKE_MODULE_PATH}/unexported_symbols.txt
		# 		${CMAKE_CURRENT_BINARY_DIR}/CMakeFiles/${TARGET_NAME}.dir/${LINK_CMD_FILE}
		# 	COMMENT "Unexport symbols in ${PROJECT_NAME}"	
		# )
    endif()
endfunction()