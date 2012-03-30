'''
GTS ( General Terminal Scripter ) 

@author: starofrainnight
@date: 2012-3-30
'''

import time
import win32pipe
import win32file
import pywintypes
import collections
import string
import rabird.compatible

PIPE_ACCESS_DUPLEX = 0x3
PIPE_TYPE_MESSAGE = 0x4
PIPE_READMODE_MESSAGE = 0x2
PIPE_WAIT = 0
PIPE_NOWAIT = 1
PIPE_UNLIMITED_INSTANCES = 255
BUFSIZE = 4096
NMPWAIT_USE_DEFAULT_WAIT = 0
INVALID_HANDLE_VALUE = -1
ERROR_PIPE_CONNECTED = 535

class scripter_t(rabird.compatible.unicode_t):
	pipe_names = [
		"\\\\.\\pipe\\terminal_scripter_input",
		"\\\\.\\pipe\\terminal_scripter_output"
		]	

	def __init__(self):
		super(scripter_t,self).__init__()
		
		self.pipe_handles = [0, 0]
		
		for i in xrange(0, len(self.pipe_names)):
			self.pipe_handles[i] = win32pipe.CreateNamedPipe(
				self.pipe_names[i],
				PIPE_ACCESS_DUPLEX,
				PIPE_TYPE_MESSAGE |	PIPE_READMODE_MESSAGE |	PIPE_NOWAIT,
				PIPE_UNLIMITED_INSTANCES,
				BUFSIZE, BUFSIZE,
				NMPWAIT_USE_DEFAULT_WAIT,
				None
				)
	
		if not self.pipe_handles[i]:
			print "Error in creating Named Pipe"
			exit()

		self.output_pipe = self.pipe_handles[0]
		self.input_pipe = self.pipe_handles[1]
		# All buffers need to split into command lines
		self.raw_buffers = collections.deque()

	def wait_for_connection(self, timeout = None):
		elapsed_time = 0.0
		# Wait terminal scripter connect to us.
		while 1:
			try:
				time.sleep(0.1)
				if timeout is not None:
					elapsed_time = elapsed_time + 0.1 
					if elapsed_time > timeout:
						break
				
				win32file.WriteFile(self.output_pipe, '\n')
				# If we successed detected client connected, we break this 
				# waiting loop.
				return True
			except pywintypes.error:
				# Ignored any errors
				pass
			
		return False
	
	def send_begin(self):
		win32file.WriteFile(self.output_pipe, '@begin\n')
		
	def send_end(self):
		win32file.WriteFile(self.output_pipe, '@end\n')
		
	def send(self, command):
		win32file.WriteFile(self.output_pipe, '#' + command + '\n')
		
	def wait_for_strings(self, strings):
		self.send_begin()
		self.send('wait_for_strings')
		for c in strings:
			self.send(c)
		self.send_end()
		
	##
	#
	# Wait for a command
	#
	# @return:  If successed, a new command will be returned. If pipe be disconnected, 
	# a None will be returned.
	def wait_for_command(self):
		readed_size = 0
		readed_buffer = "" 
		a_line = ""
		a_command = None
		sub_index = 0
		while 1:
			time.sleep(0.1)
			try:
				readed_size, readed_buffer = win32file.ReadFile(input_pipe, 1024)
				while len(readed_buffer) > 0:
					a_line = ""
					sub_index = readed_buffer.find('\n')
					if sub_index == 0:
						if len(self.raw_buffers) > 0:
							a_line = string.join(self.raw_buffers)
							self.raw_buffers.clear()
							readed_buffer = readed_buffer[(sub_index+1):len(readed_buffer)]
					elif sub_index > 0:
						sub_string = readed_buffer[0:sub_index].strip('\n\r')
						if len(sub_string) > 0:
							self.raw_buffers.append(sub_string)
							
						if len(self.raw_buffers) > 0:
							a_line = string.join(self.raw_buffers)
							
						self.raw_buffers.clear()
						readed_buffer = readed_buffer[(sub_index+1):len(readed_buffer)]
					else:
						sub_string = readed_buffer.strip('\n\r')
						if len(sub_string) > 0:
							self.raw_buffers.append(sub_string)
						break
					
					if len(a_line) > 0:
						if cmp(a_line, "@begin") == 0:
							a_command = []
						elif cmp(a_line, "@end") == 0:
							if a_command is not None:
								return a_command
						elif a_command is not None:
							a_command.append(a_line)
			except pywintypes.error as e:
				if 109 == e[0]:
					# Remote pipe disconnected.
					return None
				elif 232 == e[0]:
					# Nothing could read from input pipe
					pass
				else:
					raise e;
				
