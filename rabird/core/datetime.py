'''
@date 2013-5-12

@author Hong-She Liang <starofrainnight@gmail.com>
'''


import time
import ctypes
import copy
import abc
import sys
import time
import six

if sys.platform == 'win32':
    import win32api
else:
    from linux_metrics import cpu_stat


class CpuTimes(object):

    def __init__(self):
        super(CpuTimes, self).__init__()
        self.wall = 0
        self.user = 0
        self.system = 0


@six.add_metaclass(abc.ABCMeta)
class AbstractCpuTimer(object):

    def __init__(self):
        super(AbstractCpuTimer, self).__init__()

        self.__is_stopped = True
        # Cpu times, a protected member, could be access by sub-classes
        self._cpu_times = CpuTimes()

    def is_stopped(self):
        return self.__is_stopped

    def start(self):
        self.__is_stopped = False
        self._cpu_times = CpuTimes()

    def stop(self):
        self.__is_stopped = True

    def elapsed(self):
        return copy.deepcopy(self._cpu_times)

    def resume(self):
        self.__is_stopped = False


class CpuTimer(AbstractCpuTimer):

    def __init__(self):
        super(CpuTimer, self).__init__()

        self.__max_ticks = get_cpu_ticks_max()
        self.__old_ticks = get_cpu_ticks()
        self.__ticks_per_second = get_cpu_ticks_per_second()

    def start(self):
        super(CpuTimer, self).start()
        self.__old_ticks = get_cpu_ticks()

    def elapsed(self):
        new_ticks = get_cpu_ticks()
        delta_ticks = get_cpu_ticks_different(self.__old_ticks, new_ticks)
        self._cpu_times.wall += cpu_ticks_to_time(delta_ticks)
        self.__old_ticks = new_ticks
        return super(CpuTimer, self).elapsed()

    def stop(self):
        self.elapsed()

        super(CpuTimer, self).stop()

    def resume(self):
        self.__old_ticks = get_cpu_ticks()
        super(CpuTimer, self).resume()


def __get_cpu_ticks_per_second_win32():
    return 1000


def __get_cpu_ticks_max_win32():
    return 0xFFFFFFFF


def __get_cpu_ticks_win32():
    # FIXED: win32api.GetTickCount()'s value will be converted to an 32bits
    # integer ! It must be DWORD not integer! We convert it back to unsigned
    # value.
    return (win32api.GetTickCount() + 0x100000000) % 0x100000000


def __get_cpu_ticks_per_second_unix():
    return 100


def __get_cpu_ticks_max_unix():
    return 0xFFFFFFFF


def __get_cpu_ticks_unix():
    cpu_times = cpu_stat.cpu_times()
    total_ticks = 0
    for i in range(0, 7):
        total_ticks += cpu_times[i]
    return total_ticks


def get_cpu_ticks_different(ticks_before, ticks_after):
    return (ticks_after - ticks_before + (get_cpu_ticks_max() + 1)) % (get_cpu_ticks_max() + 1)


def cpu_ticks_to_time(ticks):
    return float(ticks) / get_cpu_ticks_per_second()

if sys.platform == 'win32':
    get_cpu_ticks = __get_cpu_ticks_win32
    get_cpu_ticks_per_second = __get_cpu_ticks_per_second_win32
    get_cpu_ticks_max = __get_cpu_ticks_max_win32
else:
    get_cpu_ticks = __get_cpu_ticks_unix
    get_cpu_ticks_per_second = __get_cpu_ticks_per_second_unix
    get_cpu_ticks_max = __get_cpu_ticks_max_unix

##
# A class that determine if we need to sleep for a while to achieve
# expected time.
#
# Because the python's execution is not time sensitive, if we need
# to do something more precisely to the final expected time step
# by step, we have to sleep to wait for current expected step time
# or not to sleep for let the expected time catch up.
#
# This class implemented all stuffs we must care about, and provided
# a simply interface to handle the suitation.
#


class StepSleeper(object):

    def __init__(self):
        super(StepSleeper, self).__init__()
        self.__cpu_timer = CpuTimer()
        self.__final_expected_time = None
        self.__slice_time = None
        self.__next_expected_time = None
        self.__times_to_next_action = 1
        self.__times = 0

    def start(self, expected_time, slice_time):
        self.__final_expected_time = expected_time
        self.__next_expected_time = slice_time
        self.__slice_time = slice_time
        self.__times_to_next_action = 1
        self.__times = 0
        self.__cpu_timer.start()

    def step(self):
        self.__times += 1
        self.__next_expected_time += self.__slice_time
        if self.__times < self.__times_to_next_action:
            return

        self.__times = 0

        cpu_times = self.__cpu_timer.elapsed()
        if cpu_times.wall > self.__next_expected_time:
            self.__times_to_next_action += 1
            return

        time.sleep(self.__next_expected_time - cpu_times.wall)

    def stop(self):
        self.__cpu_timer.stop()
