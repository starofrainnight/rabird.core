

# #
# pywin32 actially do not support unicode version of windows api, just as if
# you input the multilanguage ( mix different language characters ). for ex:
# the api GetCommandLine() will return a string object decoded by current locale,
# if all the characters are in the scale of locale, that's fine, it will no
# harm to the program, but if there have some characters if no in the scale of
# locale, and in the unicode scale, it's covertion will broken the finally
# string.
#
# so we have to use our "W" version apis ( unicode version apis ) to finish our
# job.
#
import sys
import traceback
import ctypes
import ctypes.wintypes
import six

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_RDWR = GENERIC_READ | GENERIC_WRITE
TOKEN_QUERY = 8
SECURITY_MAX_SID_SIZE = 68
WinBuiltinAdministratorsSid = 26
ERROR_NO_SUCH_LOGON_SESSION = 1312
ERROR_PRIVILEGE_NOT_HELD = 1314
TokenLinkedToken = 19
SEE_MASK_NOCLOSEPROCESS = 0x00000040
SEE_MASK_NOASYNC = 0x00000100
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1)


def _errcheck_bool(value, func, args):
    if not value:
        raise ctypes.WinError()
    return args


def _errcheck_handle(value, func, args):
    if not value:
        raise ctypes.WinError()
    if value == INVALID_HANDLE_VALUE:
        raise ctypes.WinError()
    return args


def _errcheck_dword(value, func, args):
    if value == 0xFFFFFFFF:
        raise ctypes.WinError()
    return args


class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = (
        ("cbSize", ctypes.wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", ctypes.wintypes.HANDLE),
        ("lpVerb", ctypes.c_wchar_p),
        ("lpFile", ctypes.c_wchar_p),
        ("lpParameters", ctypes.c_wchar_p),
        ("lpDirectory", ctypes.c_wchar_p),
        ("nShow", ctypes.c_int),
        ("hInstApp", ctypes.wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", ctypes.c_wchar_p),
        ("hKeyClass", ctypes.wintypes.HKEY),
        ("dwHotKey", ctypes.wintypes.DWORD),
        ("hIconOrMonitor", ctypes.wintypes.HANDLE),
        ("hProcess", ctypes.wintypes.HANDLE),
    )

try:
    ShellExecuteEx = ctypes.windll.shell32.ShellExecuteExW
except AttributeError:
    ShellExecuteEx = None
else:
    ShellExecuteEx.restype = ctypes.wintypes.BOOL
    ShellExecuteEx.errcheck = _errcheck_bool
    ShellExecuteEx.argtypes = (
        ctypes.POINTER(SHELLEXECUTEINFO),
    )

# @return an unicode string indicate the command line


def GetCommandLine():
    return ctypes.c_wchar_p(ctypes.windll.kernel32.GetCommandLineW()).value


def CommandLineToArgv(ACommandLine):
    arguments_count = ctypes.c_int()
    arguments_memory = ctypes.c_void_p(ctypes.windll.shell32.CommandLineToArgvW(
        ctypes.c_wchar_p(ACommandLine), ctypes.byref(arguments_count)))

    result = []
    if 0 != arguments_memory.value:
        for i in range(1, arguments_count.value):
            wstring_memory = ctypes.c_void_p.from_address(
                arguments_memory.value + i * ctypes.sizeof(ctypes.c_void_p))
            result.append(ctypes.wstring_at(wstring_memory.value))

    ctypes.windll.kernel32.LocalFree(arguments_memory)

    return result


def IsUserAnAdmin():
    import ctypes
    # WARNING: requires Windows XP SP2 or higher!
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        traceback.print_exc()
        return False


def RunAsAdmin(command_line, is_wait_for_finished=False, show_cmd=0):
    if type(command_line) not in (tuple, list):
        raise ValueError("command_line is not a sequence.")

    cmd = '"%s"' % (command_line[0],)
    # XXX TODO: isn't there a function or something we can call to massage
    # command line params?
    params = " ".join(['"%s"' % (x,) for x in command_line[1:]])

    execinfo = SHELLEXECUTEINFO()
    execinfo.cbSize = ctypes.sizeof(execinfo)
    execinfo.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NOASYNC
    execinfo.hwnd = None
    execinfo.lpVerb = ctypes.c_wchar_p("runas")
    execinfo.lpFile = ctypes.c_wchar_p(cmd)
    execinfo.lpParameters = ctypes.c_wchar_p(params)
    execinfo.lpDirectory = None
    execinfo.nShow = show_cmd
    ShellExecuteEx(ctypes.byref(execinfo))
    if is_wait_for_finished:
        ctypes.windll.kernel32.WaitForSingleObject(execinfo.hProcess, 1)
