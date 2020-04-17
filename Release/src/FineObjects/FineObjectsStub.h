#pragma once 

#include <SDKDDKVer.h>

#define FINEOBJ_VERSION 12014
extern const __declspec(selectany) int UserModuleFineObjVersion = FINEOBJ_VERSION;

#if !defined( _MT )
	#error FineObjects can not be used with single-threaded runtime libraries
#endif

// Макросы для заголовков Platform SDK
#define NOMINMAX

#ifndef WINVER
#define WINVER _WIN32_WINNT_WIN6
#endif
#ifndef _WIN32_IE
#define _WIN32_IE _WIN32_IE_WIN6
#endif

#ifdef _WIN32_WINNT
#	if WINVER != _WIN32_WINNT
#		error WINVER and _WIN32_WINNT must be equal
#	endif
#else
#	define _WIN32_WINNT WINVER
#endif

#ifdef _ATL_MIN_CRT
// Запрещаем использование ATL версий new и delete
#undef _ATL_MIN_CRT
#endif

// Запрещаем использование строковых функций из ShlWApi.h
// Эти функции пересекаются по именам с некоторыми нашими функциями.
// ShlWApi.h включается заголовками ATL
#ifndef NO_SHLWAPI_STRFCNS
#define NO_SHLWAPI_STRFCNS
#endif

//
// На Win64 и Win32 различная декорация имён:
// подстрочная черта на Win64 не добавляется.
//
#ifdef _WIN64
#define VARIABLE_DECORATION ""
#else
#define VARIABLE_DECORATION "_"
#endif

#pragma comment( linker, "/include:" VARIABLE_DECORATION "__FineObjDll" )
#pragma comment( linker, "/include:" VARIABLE_DECORATION "__FineObjUsed" )

// Определяем этот макрос, чтобы runtime не декларировал свои версии операторов new и delete
// В заголовках runtime операторы new и delete объявляются как dllimport
// После этого их нельзя перекрыть в FineObjects
#define _MFC_OVERRIDES_NEW