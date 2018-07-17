

##
# import this unit to fixed multilanguage read /write problems,
# it's a rarely appear problem : even you set the correct locale,
# if there are a folder / file name is mix with different language copy
# from other windows PC, you could not read / write with the correct
# name !
#
# we have to do many jobs to fix it :
#
# 1. replace the stdout / stderr / stdin file object in sys with our fixed objects
# 2. fixed the sys.argv list with GetCommandLine() api in win32
# 3. fixed os.path series problems
# 4. may be there have more we have not found yet! ...
#
# @date 2011-1-25
# @author Hong-She Liang <starofrainnight@gmail.com>
#
import sys
import os
import io
import threading
import atexit
import win32console
import win32api
import win32file
import types  # for all standard type values for buildin type()
import pickle
from . import windows_api
import time
import os.path
import six

# * replace the stdout / stderr / stdin file object in sys with our fixed objects


class StdoutThread(threading.Thread):

    def __init__(self, std_handle_type, old_stdout):
        threading.Thread.__init__(self)
        # so that if the main thread exit, our thread will also exit
        self.setDaemon(True)
        self.stdout_pipe = os.pipe()
        self.file_descriptor = self.stdout_pipe[0]
        self.std_handle_type = std_handle_type
        self.old_stdout = old_stdout

        # use for internal purpose
        self.screen_buffer = win32console.GetStdHandle(self.std_handle_type)
        # do not open the file in text mode, otherwise it will try to decode
        # with the encoding, but the unicode sometimes included something
        # do not in the encoding scale, that will case a convertion error:
        # 'ascii' codec can't encode character u'\xbb' in position ...
        self.stdout = io.open(self.file_descriptor, mode='rb')
        self.stdin = None

    def run(self):
        self.stdin = StdioFile(self.stdout_pipe[1], "wb")
        if self.std_handle_type == win32api.STD_OUTPUT_HANDLE:
            sys.stdout = self.stdin
        elif self.std_handle_type == win32api.STD_ERROR_HANDLE:
            sys.stderr = self.stdin

        try:

            end_mark = ord(".")
            exit_mark = ord("@")

            while True:
                # it will be block here until any string coming ...
                # we shoudl be read three lines for a unit ( the pickle format
                # )
                temp_line = six.binary_type()
                a_line = six.binary_type()

                while True:
                    temp_line = self.stdout.readline()
                    a_line += temp_line

                    if len(temp_line) > 0:
                        #self.old_stdout.write('test end_mark \n')
                        if ord(temp_line[0]) == end_mark:
                            #self.old_stdout.write('end_mark! \n')
                            break

                # if outside need us to destroy our self, we exit ...
                if len(temp_line) >= 2:
                    if ord(temp_line[1]) == exit_mark:
                        break

                if not a_line:
                    continue

                s = pickle.loads(a_line)
                if len(s) <= 0:
                    continue

                #self.old_stdout.write('gogogo : %s,  %s\n' % (str(a_line), str(type(s))))

                if(type(s) == str):
                    if self.screen_buffer is not None:
                        # While debuging in Aptana Studio or some other situation,
                        # the screen buffer will contain an invalid handle lead to
                        # win32console.error be throw. We will use the old stdout
                        # to output our informations instead.
                        try:
                            self.screen_buffer.WriteConsole(s)
                        except win32console.error:
                            self.screen_buffer = None

                            # If we could not output through screen buffer, we
                            # convert the unicode string to python native string,
                            # and write directly to old stndard output.
                            self.old_stdout.write(str(s))
                    else:
                        self.old_stdout.write(str(s))
                else:
                    self.old_stdout.write(s)
        finally:
            if self.std_handle_type == win32api.STD_OUTPUT_HANDLE:
                sys.stdout = self.old_stdout
            elif self.std_handle_type == win32api.STD_ERROR_HANDLE:
                sys.stderr = self.old_stdout

    def stop(self):
        os.write(self.stdin.fileno(), ".@\n")
        self.join()


class StdioFile(io.FileIO):

    def __init__(self, name, mode='r', closefd=True):
        io.FileIO.__init__(self, name, mode, closefd)

    def write(self, value):
        if(type(value) != str):
            value = str(value)  # changed value to str

        # the line separator must be at the end of line !
        value = str(pickle.dumps(value)) + os.linesep
        io.FileIO.write(self, value)

old_stdout = sys.stdout
stdout_thread = None

old_stderr = sys.stderr
stderr_thread = None

# * finalize windows's unicode fix


def __on_exit_rabird_module():
    # Wait for console finished their output and restore original standard
    # input/output
    stdout_thread.stop()
    stderr_thread.stop()


def monkey_patch():
    global stdout_thread
    global stderr_thread

    is_patched = False

    # Fixed the sys.argv list with GetCommandLine() api in win32
    sys.argv = windows_api.CommandLineToArgv(windows_api.GetCommandLine())

    # The ez_setup.py will load the rabird library during setup, so we have
    # to check the type string not the directly type.
    if 'StdioFile' not in str(type(sys.stdout)):
        stdout_thread = StdoutThread(win32api.STD_OUTPUT_HANDLE, old_stdout)
        stdout_thread.start()
        is_patched = True

    if 'StdioFile' not in str(type(sys.stderr)):
        stderr_thread = StdoutThread(win32api.STD_ERROR_HANDLE, old_stderr)
        stderr_thread.start()
        is_patched = True

    if is_patched:
        # we must restore original standard input/output file
        atexit.register(__on_exit_rabird_module)
