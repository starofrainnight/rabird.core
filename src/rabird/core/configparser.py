'''
@date 2013-5-10

@author Hong-She Liang <starofrainnight@gmail.com>
'''

import configparser
import io
import os
import re

##
# An advance ConfigParser build on configparser.ConfigParser.
#
# Features:
#
#  * set() will automatic create section if there do not have section.
#  * Support ini files that contained unnamed section.
#  * Default to case sensitive, actually most ini files are case sensitive,
#    if you want case insensitive, just set like below:
#        object.optionxform = rabird.core.ConfigParser.optionxform
#  * Removed spaces around '=', some ini parser do not accept the spaces
#    around '='.
#  * Support comments start with '#', ';'
#  * Support empty lines
#


class ConfigParser(configparser.ConfigParser):
    UNNAMED_SECTION = '#--CONFIGPARSER-UNNAMED-SECTION--#'
    # It will transfer to empty line
    _EMPTY_OPTION = '--CONFIGPARSER-EMPTY-OPTION'
    # It will transfer to comment line
    _COMMENT_OPTION = '--CONFIGPARSER-COMMENT-OPTION'

    def __init__(self, *args, **kwargs):
        if issubclass(ConfigParser, object):
            super(ConfigParser, self).__init__(*args, **kwargs)
        else:
            configparser.ConfigParser.__init__(self, *args, **kwargs)

        # Default to case sensitive
        self.optionxform = str
        # Added default unnamed section
        self.add_section(self.UNNAMED_SECTION)

        # Because readfp() may read multi-files, there may be same section with
        # some extension lines (comments or empty lines), so we can't just
        # start a line id with 0 in readfp(), that would lead
        # DuplicateOptionError error!
        self._line_id = 0

    def set(self, section, option, value):
        if not self.has_section(section):
            self.add_section(section)

        # In 3.x, the ConfigParser is a newstyle object
        if issubclass(ConfigParser, object):
            super(ConfigParser, self).set(section, option, str(value))
        else:
            configparser.ConfigParser.set(self, section, option, str(value))

    def readfp(self, fp, *args, **kwargs):
        # if hasattr(fp, 'name'):
        # We could only use the readline() by definitions
        abuffer = '[' + self.UNNAMED_SECTION + ']' + os.linesep

        while True:
            line = fp.readline()
            if len(line) <= 0:
                break

            temp_line = line.strip()
            if len(temp_line) <= 0:
                line = (self._EMPTY_OPTION +
                        str(self._line_id) + '=#' + os.linesep)
            elif temp_line.startswith('#') or temp_line.startswith(';'):
                line = self._COMMENT_OPTION + str(self._line_id) + '=#' + line
            abuffer += line

            self._line_id += 1

        # In 3.x, the ConfigParser is a newstyle object
        fp = io.StringIO(abuffer)
        if issubclass(ConfigParser, object):
            super(ConfigParser, self).readfp(fp, *args, **kwargs)
        else:
            configparser.ConfigParser.readfp(self, fp, *args, **kwargs)

    def write(self, fileobject):
        string_io = io.StringIO()

        # In 3.x, the ConfigParser is a newstyle object
        if issubclass(ConfigParser, object):
            super(ConfigParser, self).write(string_io)
        else:
            configparser.ConfigParser.write(self, string_io)

        abuffer = string_io.getvalue()
        string_io = io.StringIO(abuffer)
        # Remove unused UNNAMED section line.
        first_line = string_io.readline()
        # Sometimes UNNAMED section do not existed,
        # For example : We new a ConfigParser, then just created named section,
        # then write it to file.
        if self.UNNAMED_SECTION in first_line:
            abuffer = abuffer[len(first_line):]

            # Eat all empty lines after unnamed section
            while True:
                first_line = string_io.readline()
                if first_line not in ['\n', '\r', '\r\n']:
                    break

                abuffer = abuffer[len(first_line):]

        # Rebuild the string io and strip spaces before and after '=' ( Avoid
        # error happends to some strict ini format parsers )
        string_io = io.StringIO(abuffer)

        # You must notice that we use "\n" not the os.linesep, because "\n" will
        # be converted to '\r\n' in window while file be opened with text mode!
        abuffer = ''
        regexp = re.compile(r'([^\[][^=]*)=(.*)')
        while True:
            line = string_io.readline()
            if len(line) <= 0:
                break

            line = line.strip()

            m = regexp.match(line)
            if m is not None:
                if m.group(1).startswith(self._EMPTY_OPTION):
                    # Emtpty line
                    abuffer += '\n'
                elif m.group(1).startswith(self._COMMENT_OPTION):
                    # Remove the prefix ' #', the rest is comments !
                    abuffer += '%s\n' % m.group(2)[2:]
                else:
                    abuffer += '%s=%s\n' % (m.group(1).strip(),
                                            m.group(2).strip())
            else:
                # Added a line separator to end of section name line.
                abuffer += "%s\n" % line

        fileobject.write(abuffer.strip())
