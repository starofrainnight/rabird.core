# -*- coding: utf-8 -*-


'''
@date 2014-4-14

Some helpful utilities use with html.

@author Hong-She Liang <starofrainnight@gmail.com>
'''

from six.moves import html_entities
from six.moves import html_parser
import six
import xml.sax.saxutils

# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;",
    '\r\n': "<BR />",
    '\r': "<BR />",
    '\n': "<BR />",
    ' ': "&nbsp;",
}
html_unescape_table = {v: k for k, v in list(html_escape_table.items())}
for k, v in list(html_entities.codepoint2name.items()):
    html_unescape_table['&%s;' % (v)] = chr(k)


def escape(text):
    return xml.sax.saxutils.escape(text)


def unescape(text):
    return xml.sax.saxutils.unescape(text)


def display_escape(text):
    return xml.sax.saxutils.escape(text, html_escape_table)


def display_unescape(text):
    output_text = ''

    i = 0
    while(i < len(text)):
        try:
            skip_len = 0
            for k, v in list(html_unescape_table.items()):
                if text[i:i + len(k)] == k:
                    skip_len = len(k) - 1
                    output_text += v
                    break

            if skip_len <= 0:
                output_text += text[i]

            i += skip_len
        finally:
            i += 1

    return xml.sax.saxutils.unescape(output_text)
