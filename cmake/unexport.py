#!/usr/bin/python
# coding: utf8
# Скрипт, позволяющий убрать экспорт некоторых функций из динамических библиотек
# Использует генерируемый cmake-ом link.txt, генерирует VersionScript и перелинковывает с ним

import sys
import subprocess
import os
import re

gccToolchainStr = '--gcc-toolchain='

def printRed(msg):
    print("\033[91m {}\033[00m".format(msg))

# Тупо находим в build.make значение переменной по ее имени 
def getVariableValue(varName, lines):
    result = ''
    parseLine = False
    for line in lines:
        if parseLine:
            if line.endswith('\\'):
                result += line[0:-1]
            else:
                result += line
                break
        elif line.startswith(varName):
            if not line.endswith('\\'):
                return ''
            parseLine = True
            continue
    
    return result

# Получаем команду линковки из cmake-generated файлов.
# Под виндой и под линуксом cmake работает по разному, генерируя разные файлы.
def getLinkerCommand(fileName, libraryFileName):
    if os.name == 'posix':
        # берем из link.txt
        with open(sys.argv[3]) as f:
            return f.readlines()[0].strip()
    else:
        # берем из build.make
        with open(sys.argv[3]) as f:
            # Сплитим на линии
            lines = [line for line in f.read().splitlines() if line]
            # Ищем команду линковки
            linkerCommand = ''
            for line in lines:
                if line.find('-o %s' % libraryFileName) != -1:
                    linkerCommand = line.strip()
                    break
            # Заменяем имена переменных в команде на их значения
            return re.sub(r'\$\((\w+)\)', lambda m: getVariableValue(m.group(1), lines), linkerCommand)
        
# Запускаем команды и возвращаем вывод в stdout
def runCmd(cmd):
    # WORKAROUND
    # Решаем проблему длинных путей на Windows
    # На Windows максимальная длина пути 8191 символ
    # Команды линковки могут быть длиннее
    # Используем возможность read-options-from-file имеющуюся у clang
    # Cуть в том чтобы записать аргументы в файл и передать имя файла в качестве аргумента
    # Например: clang.exe @filename (символ @ как раз говорит что в файле аргументы)
    if len(cmd) > 8000 and os.name == 'nt':
        # Не будет работать, если в пути содержатся пробелы
        tokens = cmd.split()
        assert len(tokens) > 1
        cmd_prefix = tokens[0]

        # Часто команды линковски идут в виде:
        # cd <somepath> && <clangpath>\clang++.exe <clang args>
        # Поэтому мы проверяем что это такой случай и в файл пишем только <clang args>
        # Если <somepath> и/или <clangpath> будут с пробелами то работать не будет
        if tokens[0] == 'cd' and tokens[2] == '&&':
            cmd_prefix = ' '.join(tokens[0:4])

        cmd_suffix = cmd[len(cmd_prefix) + 1:]

        argsfilename = 'args.cflags'
        argsFile = open(argsfilename, 'w')
        argsFile.write(cmd_suffix)
        argsFile.close()

        cmd = "{} @{}".format(cmd_prefix, argsfilename)

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = proc.communicate()
    if proc.returncode:
        printRed('Error in command!')
        print(cmd)
        return (False, res[1])
    return (True, res[0])


# Читаем символы которые не экспортируются
def readUnexportSymsFile(fileName):
    syms = set()
    with open(fileName) as file:
        for line in file:
            sym = line.strip()
            if sym:
                syms.add(sym)
    return syms

# Создаем version_script файл
def generateVersionScript(syms, libFileName, unexportedSyms):
    (dir, name) = os.path.split(libFileName)
    fileName = os.path.join(dir, name + '.ver')
    fileName = os.path.normpath(fileName)
    file = open(fileName, 'w')
    file.write('VERSION_1.0\n{\n\tglobal:\n')
    for sym in syms:
        if sym not in unexportedSyms:
            if '@' in sym:
                # В выводе arm64 nm иногода через @@ пишется название библиотеки. Это недопустимый
                # сммвол в VersionScript
                file.write(sym.split('@')[0] + ';\n')
            else:
                file.write(sym + ';\n')

    file.write('\n\tlocal: *;\n};')
    file.close()
    return fileName


# Получаем список символов библиотеки. Пустой список в случае неудачи.
def getSymbols(libName, nmPath):
    symbols = []
    res = runCmd(nmPath + " -g " + libName)
    if not res[0]:
        printRed("Error in getting symbols!")
        return symbols

    lines = res[1].split(b'\n')
    for line in lines:
        s = line.decode('utf-8')
        if s:
            symbols.append(s.split()[-1])
    return symbols

    
# Ищет первую подходящую по суффиксу команду в toolchain дирректории (nm, strip...)
def getToolchainCmd(toolchainDir, cmdSuffix):
    if os.name == 'nt':
        cmdSuffix += '.exe'
        
    result = os.path.join(toolchainDir, 'bin')
    print(result)
    exist = False
    for fname in os.listdir(result):
        if fname[-len(cmdSuffix):] == cmdSuffix:
            result = os.path.join(result, fname)
            exist = True
            break

    if not exist:
        return ''
    return result
    
##########################################
def main():
    
    # Получаем команду линковки из файла link.txt
    linkerCommand = getLinkerCommand(sys.argv[3], sys.argv[1])
    if not linkerCommand:
        printRed('Linker command is empty!')
        return -1
        
    # Определяем путь к утилитами strip/nm если винда на хосте
    nmPath = ''
    if os.name == 'nt':
        linkCmdList = linkerCommand.split()
        # Получаем тулчейн директорию
        toolchainDir = ''
        for item in linkCmdList:
            pos = item.find(gccToolchainStr)
            if pos != -1:
                toolchainDir = os.path.normpath(item[len(gccToolchainStr):])
                break
        if not toolchainDir:
            printRed('No toolchain dir in link command!')
            return -1
        
        # Ищем nm в дирректории с утилитами для сборки
        nmPath = getToolchainCmd(toolchainDir, 'nm')
        
    elif os.name == 'posix':
        # Под линупсом просто nm из /usr/bin
        nmPath = 'nm'
    else:
        printRed('Unknown host OS!')
        return -1
    
    # Читаем символы, которые надо сделать локальными
    unexportedSyms = readUnexportSymsFile(sys.argv[2])
    
    # Читаем символы библиотеки
    symbols = getSymbols(sys.argv[1], nmPath)
    if not symbols:
        return -1
    
    # Генерируем version-script файл
    versionFileName = generateVersionScript(symbols, sys.argv[1], unexportedSyms)
    
    # Перелинковываем бинарник c version-script файлом
    linkerCommand += ' -Wl,--version-script=%s' % versionFileName
    result = runCmd(linkerCommand)
    if not result[0]:
        printRed('Linking command error! ')
        printRed(result[1])
        return -1
    
    return 0


######################################################
if __name__ == "__main__":
    sys.exit(main())
