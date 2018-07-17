

import sys
import os
import glob

logger = __import__('logging').getLogger('rabird.core.system')

if sys.platform == "win32":
    from . import windows_api


def get_single_argument_win32():
    command_line = rabird.core.windows_api.GetCommandLine().strip()

    script_file_name = os.path.basename(sys.argv[0])
    pos = command_line.rfind(script_file_name)

    result = ""
    if pos >= 0:
        begin_index = pos + len(script_file_name) + 1
        end_index = len(command_line)
        result = command_line[begin_index:end_index].strip()
        if len(result) > 0:
            if result[0] == "\"":
                result = result[1:len(result) - 1]

    return result


def get_single_argument_others():
    result = ""
    if len(sys.argv) > 2:
        result = sys.argv[1]

    return result


def execute(command):
    logger.info('Executing: %s' % command)
    os.system(command)


def whereis_win32(file_name):
    result = []

    file_name = os.path.splitext(file_name)[0]

    pathexts = os.environ["PATHEXT"].split(os.pathsep)
    original_paths = os.environ["PATH"].split(os.pathsep)

    # Make paths unique!
    paths = []
    for apath in original_paths:
        apath = os.path.normpath(apath)
        if apath not in paths:
            paths.append(apath)

    for apath in paths:
        if not os.path.exists(apath):
            continue

        if not os.path.isdir(apath):
            continue

        for aext in pathexts:
            exe_paths = glob.glob(os.path.join(
                apath, "%s%s" % (file_name, aext)))
            for aexe_path in exe_paths:
                splitted = os.path.splitext(os.path.basename(apath))
                if splitted[0].lower() != file_name.lower():
                    continue

                result.append(aexe_path)

    return result


def whereis_unix(file_name):
    result = []

    file_name = os.path.splitext(file_name)[0]
    original_paths = os.environ["PATH"].split(os.pathsep)

    # Make paths unique!
    paths = []
    for apath in original_paths:
        apath = os.path.normpath(apath)
        if apath not in paths:
            paths.append(apath)

    for apath in paths:
        if not os.path.exists(apath):
            continue

        if not os.path.isdir(apath):
            continue

        if (os.stat(apath).st_mode & stat.S_IXUSR) == 0:
            continue

        splitted = os.path.splitext(os.path.basename(apath))
        if splitted[0].lower() != file_name:
            continue

        result.append(apath)

    return result

if sys.platform == "win32":
    whereis = whereis_win32
    get_single_argument = get_single_argument_win32
else:
    whereis = whereis_unix
    get_single_argument = get_single_argument_others
