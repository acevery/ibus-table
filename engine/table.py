# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# IBus-Table - The Tables engine for IBus
#
# Copyright (c) 2008-2013 Yuwei Yu <acevery@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# $Id: $
#
__all__ = (
    "EngineTable",
)

import os
#from ibus import Property

from gi.repository import IBus
import tabdict

import re
patt_edit = re.compile(r'(.*)###(.*)###(.*)')
patt_uncommit = re.compile(r'(.*)@@@(.*)')

from gettext import dgettext
_  = lambda a : dgettext("ibus-table", a)
N_ = lambda a : a

import string
# handy functions
def ispunct(c): return IBus.keyval_to_unicode(c) in string.punctuation
def isdigit(c): return IBus.keyval_to_unicode(c) in string.digits

from gi.repository import GLib
def variant_to_value(variant):
    if type(variant) != GLib.Variant:
        return variant
    type_string = variant.get_type_string()
    if type_string == 's':
        return variant.get_string()
    elif type_string == 'i':
        return variant.get_int32()
    elif type_string == 'b':
        return variant.get_boolean()
    elif type_string == 'as':
        # In the latest pygobject3 3.3.4 or later, g_variant_dup_strv
        # returns the allocated strv but in the previous release,
        # it returned the tuple of(strv, length)
        if type(GLib.Variant.new_strv([]).dup_strv()) == tuple:
            return variant.dup_strv()[0]
        else:
            return variant.dup_strv()
    else:
        print 'error: unknown variant type:', type_string
    return variant

__half_full_table = [
    (0x0020, 0x3000, 1),
    (0x0021, 0xFF01, 0x5E),
    (0x00A2, 0xFFE0, 2),
    (0x00A5, 0xFFE5, 1),
    (0x00A6, 0xFFE4, 1),
    (0x00AC, 0xFFE2, 1),
    (0x00AF, 0xFFE3, 1),
    (0x20A9, 0xFFE6, 1),
    (0xFF61, 0x3002, 1),
    (0xFF62, 0x300C, 2),
    (0xFF64, 0x3001, 1),
    (0xFF65, 0x30FB, 1),
    (0xFF66, 0x30F2, 1),
    (0xFF67, 0x30A1, 1),
    (0xFF68, 0x30A3, 1),
    (0xFF69, 0x30A5, 1),
    (0xFF6A, 0x30A7, 1),
    (0xFF6B, 0x30A9, 1),
    (0xFF6C, 0x30E3, 1),
    (0xFF6D, 0x30E5, 1),
    (0xFF6E, 0x30E7, 1),
    (0xFF6F, 0x30C3, 1),
    (0xFF70, 0x30FC, 1),
    (0xFF71, 0x30A2, 1),
    (0xFF72, 0x30A4, 1),
    (0xFF73, 0x30A6, 1),
    (0xFF74, 0x30A8, 1),
    (0xFF75, 0x30AA, 2),
    (0xFF77, 0x30AD, 1),
    (0xFF78, 0x30AF, 1),
    (0xFF79, 0x30B1, 1),
    (0xFF7A, 0x30B3, 1),
    (0xFF7B, 0x30B5, 1),
    (0xFF7C, 0x30B7, 1),
    (0xFF7D, 0x30B9, 1),
    (0xFF7E, 0x30BB, 1),
    (0xFF7F, 0x30BD, 1),
    (0xFF80, 0x30BF, 1),
    (0xFF81, 0x30C1, 1),
    (0xFF82, 0x30C4, 1),
    (0xFF83, 0x30C6, 1),
    (0xFF84, 0x30C8, 1),
    (0xFF85, 0x30CA, 6),
    (0xFF8B, 0x30D2, 1),
    (0xFF8C, 0x30D5, 1),
    (0xFF8D, 0x30D8, 1),
    (0xFF8E, 0x30DB, 1),
    (0xFF8F, 0x30DE, 5),
    (0xFF94, 0x30E4, 1),
    (0xFF95, 0x30E6, 1),
    (0xFF96, 0x30E8, 6),
    (0xFF9C, 0x30EF, 1),
    (0xFF9D, 0x30F3, 1),
    (0xFFA0, 0x3164, 1),
    (0xFFA1, 0x3131, 30),
    (0xFFC2, 0x314F, 6),
    (0xFFCA, 0x3155, 6),
    (0xFFD2, 0x315B, 9),
    (0xFFE9, 0x2190, 4),
    (0xFFED, 0x25A0, 1),
    (0xFFEE, 0x25CB, 1)]

def unichar_half_to_full (c):
    code = ord (c)
    for half, full, size in __half_full_table:
        if code >= half and code < half + size:
            return unichr (full + code - half)
    return c

class KeyEvent:
    def __init__(self, keyval, is_press, state):
        self.code = keyval
        self.mask = state
        if not is_press:
            self.mask |= IBus.ModifierType.RELEASE_MASK
    def __str__(self):
        return "%s 0x%08x" % (IBus.keyval_name(self.code), self.mask)


class Editor(object):
    '''Hold user inputs chars and preedit string'''
    def __init__(self, config, phrase_table_index, valid_input_chars,
                 max_key_length, database,
                 parser=tabdict.parse, deparser=tabdict.deparse, max_length=64):
        self.db = database
        self._config = config
        self._name = self.db.get_ime_property('name')
        self._config_section = "engine/Table/%s" % self._name.replace(' ','_')
        self._pt = phrase_table_index
        self._parser = parser
        self._deparser = deparser
        self._max_key_len = int(max_key_length)
        self._max_length = max_length
        self._valid_input_chars = valid_input_chars
        #
        # below vals will be reset in self.clear()
        #
        # we hold this: [str,str,...]
        # self._chars: hold user input in table mode (valid,invalid,prevalid)
        self._chars = [[],[],[]]
        #self._t_chars: hold total input for table mode for input check
        self._t_chars = []
        # self._u_chars: hold user input but not manual comitted chars
        self._u_chars = []
        # self._tabkey_list: hold tab_key objects transform from user
        #     input chars
        self._tabkey_list = []
        # self._strings: hold preedit strings
        self._strings = []
        # self._cursor: the caret position in preedit phrases
        self._cursor = [0,0]
        # self._candidates: hold candidates selected from database [[now],[pre]]
        self._candidates = [[],[]]
        # self._lookup_table_size: how many candidates we should hold in ui
        self._lookup_table_size = variant_to_value(
            self._config.get_value(self._config_section,
                                   "LookupTableSize")
        )
        if self._lookup_table_size == None:
            self._lookup_table_size = 6


        self._orientation = variant_to_value(self._config.get_value(
                self._config_section,
                "LookupTableOrientation"))
        if self._orientation == None:
            # 0, virtical
            # 1, horizontal
            # 2, system default
            self._orientation = 0

        self._lookup_table = IBus.LookupTable.new(
            page_size=self._lookup_table_size,
            cursor_pos=0,
            cursor_visible=True,
            round=True
        )
        self._lookup_table.set_orientation(self._orientation)
        # self._py_mode: whether in pinyin mode
        self._py_mode = False
        # self._zi: the last Zi commit to preedit
        self._zi = u''
        # self._caret: caret position in lookup_table
        self._caret = 0
        # self._onechar: whether we only select single character
        self._onechar = variant_to_value(
            self._config.get_value(self._config_section,
                                   "OneChar")
        )
        if self._onechar == None:
            self._onechar = False

        # self._auto_select: select automatically the first phrase
        self._auto_select = variant_to_value(
            self._config.get_value(self._config_section,
                                   "AutoSelect")
        )
        if self._auto_select == None:
            self._auto_select = self.db.get_ime_property(
                'auto_select').lower() == u'true'

        # self._chinese_mode: the candidate filter mode,
        #   0 is simplify Chinese
        #   1 is traditional Chinese
        #   2 is Big charset mode, but simplify Chinese first
        #   3 is Big charset mode, but traditional Chinese first
        #   4 is Big charset mode.
        # we use LC_CTYPE or LANG to determine which one to use
        self._chinese_mode = variant_to_value(self._config.get_value(
            self._config_section,
            "ChineseMode"))
        if self._chinese_mode == None:
            self._chinese_mode = self.get_chinese_mode()

    def get_chinese_mode(self):
        '''Use db value or LC_CTYPE in your box to determine the _chinese_mode'''
        # use db value, if applicable
        __db_chinese_mode = self.db.get_chinese_mode()
        if __db_chinese_mode >= 0:
            return __db_chinese_mode
        # otherwise
        try:
            if os.environ.has_key('LC_CTYPE'):
                __lc = os.environ['LC_CTYPE'].split('.')[0].lower()
            else:
                __lc = os.environ['LANG'].split('.')[0].lower()

            if __lc.find('_cn') != -1:
                return 0
            # hk and tw is should use tc as default
            elif (__lc.find('_hk') != -1 or __lc.find('_tw') != -1
                  or __lc.find('_mo') != -1):
                return 1
            else:
                if self.db._is_chinese:
                    # if IME declare as Chinese IME
                    return 0
                else:
                    return -1
        except:
            return -1

    def change_chinese_mode(self):
        if self._chinese_mode != -1:
            self._chinese_mode = (self._chinese_mode +1) % 5
        self._config.set_value(
            self._config_section,
            "ChineseMode",
            GLib.Variant.new_int32(self._chinese_mode))

    def clear(self):
        '''Remove data holded'''
        self.over_input()
        self._t_chars = []
        self._strings = []
        self._cursor = [0,0]
        self._py_mode = False
        self._zi = u''
        self.update_candidates

    def is_empty(self):
        return len(self._t_chars) == 0

    def clear_input(self):
        '''
        Remove input characters held for Table mode,
        '''
        self._chars = [[],[],[]]
        self._tabkey_list = []
        self._lookup_table.clear()
        self._lookup_table.set_cursor_visible(True)
        self._candidates = [[],[]]

    def over_input(self):
        '''
        Remove input characters held for Table mode,
        '''
        self.clear_input()
        self._u_chars = []

    def set_parser(self, parser):
        '''change input parser'''
        self.clear()
        self._parser = parser

    def add_input(self,c):
        '''add input character'''
        if len(self._t_chars) == self._max_length:
            return True
        self._zi = u''
        if self._cursor[1]:
            self.split_phrase()
        if ((len(self._chars[0]) == self._max_key_len and (not self._py_mode))
            or
            (len(self._chars[0]) == 7 and self._py_mode)):
            self.auto_commit_to_preedit()
            res = self.add_input (c)
            return res
        elif self._chars[1]:
            self._chars[1].append(c)
        else:
            if ((not self._py_mode and (c in self._valid_input_chars))
                or
                (self._py_mode and (c in u'abcdefghijklmnopqrstuvwxyz!@#$%'))):
                try:
                    self._tabkey_list += self._parser(c)
                    self._chars[0].append(c)
                except:
                    self._chars[1].append(c)
            else:
                self._chars[1].append(c)
        self._t_chars.append(c)
        res = self.update_candidates()
        return res

    def pop_input(self):
        '''remove and display last input char held'''
        _c =''
        if self._chars[1]:
            _c = self._chars[1].pop()
        elif self._chars[0]:
            _c = self._chars[0].pop()
            self._tabkey_list.pop()
            if (not self._chars[0]) and self._u_chars:
                self._chars[0] = self._u_chars.pop()
                self._chars[1] = self._chars[1][:-1]
                self._tabkey_list = self._parser(self._chars[0])
                self._strings.pop(self._cursor[0] - 1 )
                self._cursor[0] -= 1
        self._t_chars.pop()
        self.update_candidates()
        return _c

    def get_input_chars(self):
        '''get characters held, valid and invalid'''
        return self._chars[0] + self._chars[1]

    def get_input_chars_string(self):
        '''Get valid input char string'''
        return u''.join(map(str, self._t_chars))

    def get_all_input_strings(self):
        '''Get all uncommit input characters, used in English mode or direct
        commit

        '''
        return  u''.join(map(u''.join, self._u_chars + [self._chars[0]] +
                             [self._chars[1]]))

    def get_index(self,key):
        '''Get the index of key in database table'''
        return self._pt.index(key)

    def split_phrase(self):
        '''Splite current phrase into two phrase'''
        _head = u''
        _end = u''
        try:
            _head = self._strings[self._cursor[0]][:self._cursor[1]]
            _end = self._strings[self._cursor[0]][self._cursor[1]:]
            self._strings.pop(self._cursor[0])
            self._strings.insert(self._cursor[0],_head)
            self._strings.insert(self._cursor[0]+1,_end)
            self._cursor[0] +=1
            self._cursor[1] = 0
        except:
            pass

    def remove_before_string(self):
        '''Remove string before cursor'''
        if self._cursor[1] != 0:
            self.split_phrase()
        if self._cursor[0] > 0:
            self._strings.pop(self._cursor[0]-1)
            self._cursor[0] -= 1
        else:
            pass
        # if we remove all characters in preedit string, we need to
        # clear the self._t_chars
        if self._cursor == [0,0]:
            self._t_chars = []

    def remove_after_string(self):
        '''Remove string after cursor'''
        if self._cursor[1] != 0:
            self.split_phrase()
        if self._cursor[0] >= len(self._strings):
            pass
        else:
            self._strings.pop(self._cursor[0])

    def remove_before_char(self):
        '''Remove character before cursor'''
        if self._cursor[1] > 0:
            _str = self._strings[self._cursor[0]]
            self._strings[self._cursor[0]] = (_str[:self._cursor[1]-1] +
                                              _str[self._cursor[1]:])
            self._cursor[1] -= 1
        else:
            if self._cursor[0] == 0:
                pass
            else:
                if len(self._strings[self._cursor[0] - 1]) == 1:
                    self.remove_before_string()
                else:
                    self._strings[self._cursor[0] - 1] = self._strings[self._cursor[0] - 1][:-1]
        # if we remove all characters in preedit string,
        # we need to clear the self._t_chars
        if self._cursor == [0,0] and not self._strings:
            self._t_chars =[]

    def remove_after_char(self):
        '''Remove character after cursor'''
        if self._cursor[1] == 0:
            if self._cursor[0] == len(self._strings):
                pass
            else:
                if len(self._strings[self._cursor[0]]) == 1:
                    self.remove_after_string()
                else:
                    self._strings[self._cursor[0]] = self._strings[self._cursor[0]][1:]
        else:
            if (self._cursor[1] + 1) == len(self._strings[self._cursor[0]]):
                self.split_phrase()
                self.remove_after_string()
            else:
                string = self._strings[self._cursor[0]]
                self._strings[self._cursor[0]] = string[:self._cursor[1]] + \
                                                 string[self._cursor[1] + 1: ]

    def get_invalid_input_chars(self):
        '''get invalid characters held'''
        return self._chars[1]

    def get_invalid_input_string(self):
        '''get invalid characters in string form'''
        return u''.join(self._chars[1])

    def get_preedit_strings(self):
        '''Get preedit strings'''
        if self._candidates[0]:
            if self._py_mode:
                _p_index = 8
            else:
                _p_index = self.get_index('phrase')
            _candi = u'###' + self._candidates[0][
                int(self._lookup_table.get_cursor_pos())
            ][_p_index] + u'###'
        else:
            input_chars = self.get_input_chars()
            if input_chars:
                _candi = u''.join(['###'] + map( str, input_chars) + ['###'])
            else:
                _candi = u''
        if self._strings:
            res = u''
            _cursor = self._cursor[0]
            _luc = len(self._u_chars)
            if _luc:
                _candi = _candi == u'' and u'######' or _candi
                res =u''.join(
                    self._strings[ : _cursor - _luc] +
                    [u'@@@'] +
                    self._strings[_cursor - _luc: _cursor] +
                    [_candi] +
                    self._strings[_cursor: ])
            else:
                res = u''.join(
                    self._strings[: _cursor] +
                    [_candi] +
                    self._strings[_cursor: ])
            return res
        else:
            return _candi
    def add_caret(self, addstr):
        '''add length to caret position'''
        self._caret += len(addstr)

    def get_caret(self):
        '''Get caret position in preedit strings'''
        self._caret = 0
        if self._cursor[0] and self._strings:
            map (self.add_caret,self._strings[:self._cursor[0]])
        self._caret += self._cursor[1]
        if self._candidates[0]:
            if self._py_mode:
                _p_index = 8
            else:
                _p_index = self.get_index ('phrase')
            _candi =self._candidates[0][
                int(self._lookup_table.get_cursor_pos())
            ][_p_index]
        else:
            _candi = u''.join(map(str,self.get_input_chars()))
        self._caret += len(_candi)
        return self._caret

    def arrow_left(self):
        '''Process Arrow Left Key Event.
        Update cursor data when move caret left'''
        if self.get_preedit_strings():
            if not(self.get_input_chars() or self._u_chars):
                if self._cursor[1] > 0:
                    self._cursor[1] -= 1
                else:
                    if self._cursor[0] > 0:
                        self._cursor[1] = len(
                            self._strings[self._cursor[0]-1]
                        ) - 1
                        self._cursor[0] -= 1
                    else:
                        self._cursor[0] = len(self._strings)
                        self._cursor[1] = 0
                self.update_candidates()
            return True
        else:
            return False

    def arrow_right(self):
        '''Process Arrow Right Key Event.
        Update cursor data when move caret right'''
        if self.get_preedit_strings():
            if not(self.get_input_chars() or self._u_chars):
                if self._cursor[1] == 0:
                    if self._cursor[0] == len(self._strings):
                        self._cursor[0] = 0
                    else:
                        self._cursor[1] += 1
                else:
                    self._cursor[1] += 1
                if self._cursor[1] == len(self._strings[self._cursor[0]]):
                    self._cursor[0] += 1
                    self._cursor[1] = 0
                self.update_candidates()
            return True
        else:
            return False

    def control_arrow_left(self):
        '''Process Control + Arrow Left Key Event.
        Update cursor data when move caret to string left'''
        if self.get_preedit_strings():
            if not(self.get_input_chars() or self._u_chars):
                if self._cursor[1] == 0:
                    if self._cursor[0] == 0:
                        self._cursor[0] = len(self._strings) - 1
                    else:
                        self._cursor[0] -= 1
                else:
                    self._cursor[1] = 0
                self.update_candidates()
            return True
        else:
            return False

    def control_arrow_right(self):
        '''Process Control + Arrow Right Key Event.
        Update cursor data when move caret to string right'''
        if self.get_preedit_strings():
            if not(self.get_input_chars() or self._u_chars):
                if self._cursor[1] == 0:
                    if self._cursor[0] == len(self._strings):
                        self._cursor[0] = 1
                    else:
                        self._cursor[0] += 1
                else:
                    self._cursor[0] += 1
                    self._cursor[1] = 0
                self.update_candidates()
            return True
        else:
            return False
    def ap_candidate(self, candi):
        '''append candidate to lookup_table'''
        if not self._py_mode:
            _p_index = self.get_index('phrase')
            _fkey = self.get_index('m0')
        else:
            _p_index = 8
            _fkey = 1
        if self.db._is_chinese:
            _tbks = u''.join(map(self._deparser, candi[_fkey + len(self._tabkey_list): _p_index-1]))
            if self._py_mode:
                # restore tune symbol
                _tbks = _tbks.replace('!','↑1').replace('@','↑2').replace('#','↑3').replace('$','↑4').replace('%','↑5')
        else:
            _tbks = u''.join( map(self._deparser , candi[_fkey + len(self._tabkey_list) : _p_index ] ) )
        _phrase = candi[_p_index]
        # further color implementation needed :)
        # here -2 is the pos of num, -1 is the pos of . 0 is the pos of string
        #attrs = ibus.AttrList ([ibus.AttributeForeground (0x8e2626, -2, 1)])
        attrs = IBus.AttrList()
        # this is the part of tabkey
        attrs.append(IBus.attr_foreground_new(0xff1973a2, 0,
                                              len(_phrase) + len(_tbks)))
        if candi[-2] < 0:
            # this is a user defined phrase:
            attrs.append(IBus.attr_foreground_new(0xff7700c3, 0, len(_phrase)))
        elif candi[-1] > 0:
            # this is a sys phrase used by user:
            attrs.append(IBus.attr_foreground_new(0xff000000, 0, len(_phrase)))
        else:
            # this is a system phrase haven't been used:
            attrs.append(IBus.attr_foreground_new(0xff000000, 0, len(_phrase)))
        a_candidate = IBus.Text.new_from_string(_phrase + _tbks)
        a_candidate.set_attributes(attrs)
        self._lookup_table.append_candidate(a_candidate)


    def filter_candidates (self, candidates):
        '''Filter candidates if IME is Chinese'''
        #if self.db._is_chinese and (not self._py_mode):
        if not self._chinese_mode in(2,3):
            return candidates[:]
        bm_index = self._pt.index('category')
        if self._chinese_mode == 2:
            # big charset with SC first
            return  filter (lambda x: x[bm_index] & 1, candidates)\
                    +filter (lambda x: x[bm_index] & (1 << 1) and \
                            (not x[bm_index] & 1), candidates)\
                    + filter (lambda x: x[bm_index] & (1 << 2), candidates)
        elif self._chinese_mode == 3:
            # big charset with SC first
            return  filter (lambda x: x[bm_index] & (1 << 1), candidates)\
                    +filter (lambda x: x[bm_index] & 1 and\
                    (not x[bm_index] & (1<<1)) , candidates)\
                    + filter (lambda x: x[bm_index] & (1 << 2), candidates)

    def update_candidates (self):
        '''Update lookuptable'''
        # first check whether the IME have defined start_chars
        if self.db.startchars and ( len(self._chars[0]) == 1 )\
                and ( len(self._chars[1]) == 0 ) \
                and ( self._chars[0][0] not in self.db.startchars):
            self._u_chars.append ( self._chars[0][0] )
            self._strings.insert ( self._cursor[0], self._chars[0][0] )
            self._cursor [0] += 1
            self.clear_input()
        else:
            if (self._chars[0] == self._chars[2] and self._candidates[0]) \
                    or self._chars[1]:
                # if no change in valid input char or we have invalid input,
                # we do not do sql enquery
                pass
            else:
                # check whether last time we have only one candidate
                only_one_last = self.one_candidate()
                # do enquiry
                self._lookup_table.clear()
                self._lookup_table.set_cursor_visible(True)
                if self._tabkey_list:
                    # here we need to consider two parts, table and pinyin
                    # first table
                    if not self._py_mode:
                        if self.db._is_chinese :
                            bm_index = self._pt.index('category')
                            if self._chinese_mode == 0:
                                # simplify Chinese mode
                                self._candidates[0] = self.db.select_words(\
                                        self._tabkey_list, self._onechar, 1 )
                            elif self._chinese_mode == 1:
                                # traditional Chinese mode
                                self._candidates[0] = self.db.select_words(\
                                        self._tabkey_list, self._onechar, 2 )
                            else:
                                self._candidates[0] = self.db.select_words(\
                                        self._tabkey_list, self._onechar )
                        else:
                            self._candidates[0] = self.db.select_words( self._tabkey_list, self._onechar )
                    else:
                        self._candidates[0] = self.db.select_zi( self._tabkey_list )
                    self._chars[2] = self._chars[0][:]

                else:
                    self._candidates[0] =[]
                if self._candidates[0]:
                    self._candidates[0] = self.filter_candidates (self._candidates[0])
                if self._candidates[0]:
                    map(self.ap_candidate, self._candidates[0] )
                else:
                    if self._chars[0]:
                        ## old manner:
                        #if self._candidates[1]:
                        #    #print self._candidates[1]
                        #    self._candidates[0] = self._candidates[1]
                        #    self._candidates[1] = []
                        #    last_input = self.pop_input ()
                        #    self.auto_commit_to_preedit ()
                        #    res = self.add_input( last_input )
                        #    print res
                        #    return res
                        #else:
                        #    self.pop_input ()
                        #    self._lookup_table.clear()
                        #    self._lookup_table.show_cursor (False)
                        #    return False
                        ###################
                        ## new manner, we add new char to invalid input
                        ## chars
                        if not self._chars[1]:
                            # we don't have invalid input chars
                            # here we need to check the last input
                            # is a punctuation or not, if is a punct,
                            # then we use old maner to summit the former valid
                            # candidate
                            if ispunct(self._chars[0][-1].encode('ascii')) \
                                    or len(self._chars[0][:-1]) \
                                    in self.db.pkeylens \
                                    or only_one_last \
                                    or self._auto_select:
                                # because we use [!@#$%] to denote [12345]
                                # in py_mode, so we need to distinguish them
                                ## old manner:
                                if self._py_mode:
                                    if self._chars[0][-1] in "!@#$%":
                                        self._chars[0].pop() 
                                        self._tabkey_list.pop()
                                        return True

                                if self._candidates[1]:
                                    self._candidates[0] = self._candidates[1]
                                    self._candidates[1] = []
                                    last_input = self.pop_input ()
                                    self.auto_commit_to_preedit ()
                                    res = self.add_input( last_input )
                                    return res
                                else:
                                    self.pop_input ()
                                    self._lookup_table.clear()
                                    self._lookup_table.set_cursor_visible(True)
                                    return False
                            else:
                                # this is not a punct or not a valid phrase
                                # last time
                                self._chars[1].append( self._chars[0].pop() )
                                self._tabkey_list.pop()
                        else:
                            pass
                        self._candidates[0] =[]
                    else:
                        self._lookup_table.clear()
                        self._lookup_table.set_cursor_visible(True)
                self._candidates[1] = self._candidates[0]

        return True

    def commit_to_preedit(self):
        '''Add select phrase in lookup table to preedit string'''
        if not self._py_mode:
            _p_index = self.get_index('phrase')
        else:
            _p_index = 8
        try:
            if self._candidates[0]:
                self._strings.insert(self._cursor[0], self._candidates[0][ self.get_cursor_pos() ][_p_index])
                self._cursor [0] += 1
                if self._py_mode:
                    self._zi = self._candidates[0][ self.get_cursor_pos() ][_p_index]
            self.over_input ()
            self.update_candidates ()
        except:
            pass

    def auto_commit_to_preedit (self):
        '''Add select phrase in lookup table to preedit string'''
        if not self._py_mode:
            _p_index = self.get_index('phrase')
        else:
            _p_index = 8
        try:
            self._u_chars.append( self._chars[0][:] )
            self._strings.insert(self._cursor[0], self._candidates[0][ self.get_cursor_pos() ][_p_index])
            self._cursor [0] += 1
            self.clear_input()
            self.update_candidates ()
        except:
            pass

    def get_aux_strings (self):
        '''Get aux strings'''
        input_chars = self.get_input_chars ()
        if input_chars:
            #aux_string =  u' '.join( map( u''.join, self._u_chars + [self._chars[0]] ) )
            aux_string =   u''.join (self._chars[0]) 
            if self._py_mode:
                aux_string = aux_string.replace('!','1').replace('@','2').replace('#','3').replace('$','4').replace('%','5')
            return aux_string

        aux_string = u''
        if self._zi:
            # we have pinyin result
            tabcodes = self.db.find_zi_code(self._zi)
            aux_string = u' '.join(tabcodes)
        #    self._zi = u''
        cstr = u''.join(self._strings)
        if self.db.user_can_define_phrase:
            if len (cstr ) > 1:
                aux_string += (u'\t#: ' + self.db.parse_phrase_to_tabkeys (cstr))
        return aux_string
    def arrow_down(self):
        '''Process Arrow Down Key Event
        Move Lookup Table cursor down'''
        res = self._lookup_table.cursor_down()
        self.update_candidates ()
        if not res and self._candidates[0]:
            return True
        return res

    def arrow_up(self):
        '''Process Arrow Up Key Event
        Move Lookup Table cursor up'''
        res = self._lookup_table.cursor_up()
        self.update_candidates ()
        if not res and self._candidates[0]:
            return True
        return res

    def page_down(self):
        '''Process Page Down Key Event
        Move Lookup Table page down'''
        res = self._lookup_table.page_down()
        self.update_candidates ()
        if not res and self._candidates[0]:
            return True
        return res

    def page_up(self):
        '''Process Page Up Key Event
        move Lookup Table page up'''
        res = self._lookup_table.page_up()
        self.update_candidates ()
        if not res and self._candidates[0]:
            return True
        return res

    def number (self, index):
        '''Select the candidates in Lookup Table
        index should start from 0'''
        self._lookup_table.set_cursor_pos_in_current_page ( index )
        if index != self._lookup_table.get_cursor_pos_in_current_page ():
            # the index given is out of range we do not commit string
            return False
        self.commit_to_preedit ()
        return True

    def alt_number (self,index):
        '''Remove the candidates in Lookup Table from user_db index should start from 0'''
        cps = self._lookup_table.get_current_page_start()
        pos = cps + index
        if  len (self._candidates[0]) > pos:
            # this index is valid
            can = self._candidates[0][pos]
            if can[-2] < 0:
                # freq of this candidate is -1, means this a user phrase
                self.db.remove_phrase (can)
                # make update_candidates do sql enquiry
                self._chars[2].pop()
                self.update_candidates ()
            return True
        else:
            return False

    def get_cursor_pos (self):
        '''get lookup table cursor position'''
        return self._lookup_table.get_cursor_pos()

    def get_lookup_table (self):
        '''Get lookup table'''
        return self._lookup_table

    def is_lt_visible (self):
        '''Check whether lookup table is visible'''
        return self._lookup_table.is_cursor_visible ()

    def backspace (self):
        '''Process backspace Key Event'''
        self._zi = u''
        if self.get_input_chars():
            self.pop_input ()
            return True
        elif self.get_preedit_strings ():
            self.remove_before_char ()
            return True
        else:
            return False

    def control_backspace (self):
        '''Process control+backspace Key Event'''
        self._zi = u''
        if self.get_input_chars():
            self.over_input ()
            return True
        elif self.get_preedit_strings ():
            self.remove_before_string ()
            return True
        else:
            return False

    def delete (self):
        '''Process delete Key Event'''
        self._zi = u''
        if self.get_input_chars():
            return True
        elif self.get_preedit_strings ():
            self.remove_after_char ()
            return True
        else:
            return False

    def control_delete (self):
        '''Process control+delete Key Event'''
        self._zi = u''
        if self.get_input_chars ():
            return True
        elif self.get_preedit_strings ():
            self.remove_after_string ()
            return True
        else:
            return False

    def l_shift (self):
        '''Process Left Shift Key Event as immediately commit to preedit strings'''
        if self._chars[0]:
            self.commit_to_preedit ()
            return True
        else:
            return False

    def r_shift (self):
        '''Proess Right Shift Key Event as changed between PinYin Mode and Table Mode'''
        self._zi = u''
        if self._chars[0]:
            self.commit_to_preedit ()
        self._py_mode = not (self._py_mode)
        return True

    def space (self):
        '''Process space Key Event
        return (KeyProcessResult,whethercommit,commitstring)'''
        if self._chars[1]:
            # we have invalid input, so do not commit 
            return (False,u'')
        if self._t_chars :
            # user has input sth
            istr = self.get_all_input_strings ()
            self.commit_to_preedit ()
            pstr = self.get_preedit_strings ()
            #print "istr: ",istr
            self.clear()
            return (True,pstr,istr)
        else:
            return (False,u'',u'')

    def one_candidate (self):
        '''Return true if there is only one candidate'''
        return len(self._candidates[0]) == 1


########################
### Engine Class #####
####################
class EngineTable(IBus.Engine):
    '''The IM Engine for Tables'''

    # colors
#    _phrase_color             = 0xffffff
#    _user_phrase_color         = 0xffffff
#    _new_phrase_color         = 0xffffff

    # lookup table page size
    _page_size = 6

    def __init__ (self, bus, obj_path, db ):
        super(EngineTable,self).__init__(connection=bus.get_connection(),
                                         object_path=obj_path)
        self._bus = bus
        # this is the backend sql db we need for our IME
        # we receive this db from IMEngineFactory
        #self.db = tabsqlitedb.tabsqlitedb( name = dbname )
        self.db = db
        # this is the parer which parse the input string to key object
        self._parser = tabdict.parse

        self._icon_dir = '%s%s%s%s' % (os.getenv('IBUS_TABLE_LOCATION'),
                os.path.sep, 'icons', os.path.sep)
        # 0 = english input mode
        # 1 = table input mode
        self._mode = 1
        # self._ime_py: True / False this IME support pinyin mode
        self._ime_py = self.db.get_ime_property ('pinyin_mode')
        if self._ime_py:
            if self._ime_py.lower() == u'true':
                self._ime_py = True
            else:
                self._ime_py = False
        else:
            print 'We coult not find "pinyin_mode" entry in database, is it a outdated database?'
            self._ime_py = False

        self._status = self.db.get_ime_property('status_prompt').encode('utf8')
        # now we check and update the valid input characters
        self._chars = self.db.get_ime_property('valid_input_chars')
        self._valid_input_chars = []
        for _c in self._chars:
            if _c in tabdict.tab_key_list:
                self._valid_input_chars.append(_c)
        del self._chars

        # check whether we can use '=' and '-' for page_down/up
        self._page_down_keys = [IBus.Page_Down, IBus.KP_Page_Down]
        self._page_up_keys = [IBus.Page_Up, IBus.KP_Page_Up]
        if '=' not in self._valid_input_chars \
                and '-' not in self._valid_input_chars:
            self._page_down_keys.append (IBus.equal)
            self._page_up_keys.append (IBus.minus)

        self._pt = self.db.get_phrase_table_index ()
        self._ml = int(self.db.get_ime_property ('max_key_length'))

        # name for config section
        self._name = self.db.get_ime_property('name')
        self._config_section = "engine/Table/%s" % self._name.replace(' ', '_')

        # config module
        self._config = self._bus.get_config ()
        self._config.connect ("value-changed", self.config_value_changed_cb)

        # Containers we used:
        self._editor = Editor(self._config, self._pt, self._valid_input_chars, self._ml, self.db)

        # some other vals we used:
        # self._prev_key: hold the key event last time.
        self._prev_key = None
        self._prev_char = None
        self._double_quotation_state = False
        self._single_quotation_state = False

        # [EnMode,TabMode] we get TabMode properties from db
        self._full_width_letter = [
            variant_to_value(
                self._config.get_value(self._config_section,
                                       "EnDefFullWidthLetter")
           ),
            variant_to_value(
                self._config.get_value(self._config_section,
                                       "TabDefFullWidthLetter")
           )
        ]
        if self._full_width_letter[0] == None:
            self._full_width_letter[0] = False
        if self._full_width_letter[1] == None:
            self._full_width_letter[1] = self.db.get_ime_property(
                'def_full_width_letter').lower() == u'true'

        self._full_width_punct = [
                variant_to_value(
                    self._config.get_value(self._config_section,
                                           "EnDefFullWidthPunct")
               ),
                variant_to_value(
                    self._config.get_value(self._config_section,
                    "TabDefFullWidthPunct")
               )
        ]
        if self._full_width_punct[0] == None:
            self._full_width_punct[0] = False
        if self._full_width_punct[1] == None:
            self._full_width_punct[1] = self.db.get_ime_property(
                'def_full_width_punct').lower() == u'true'

        # some properties we will involved, Property is taken from scim.
        #self._setup_property = Property ("setup", _("Setup"))
        self._auto_commit = variant_to_value(
            self._config.get_value(self._config_section,
                                   "AutoCommit")
       )
        if self._auto_commit == None:
            try:
                self._auto_commit = self.db.get_ime_property(
                    'auto_commit').lower() == u'true'
            except:
                self._auto_commit = False


        try:
            self._auto_select = self.db.get_ime_property('auto_select').lower() == u'true'
        except:
            self._auto_select = False
        self._auto_select = self._config.get_value (self._config_section, "AutoSelect",
                self._auto_select)

        # the commit phrases length
        self._len_list = [0]
        # connect to SpeedMeter
        #try:
        #    bus = dbus.SessionBus()
        #    user = os.path.basename( os.path.expanduser('~') )
        #    self._sm_bus = bus.get_object ("org.ibus.table.SpeedMeter.%s"\
        #            % user, "/org/ibus/table/SpeedMeter")
        #    self._sm =  dbus.Interface(self._sm_bus,\
        #            "org.ibus.table.SpeedMeter") 
        #except:
        #    self._sm = None
        #self._sm_on = False
        self._on = False
        self.reset ()

    def reset (self):
        self._editor.clear ()
        self._double_quotation_state = False
        self._single_quotation_state = False
        self._prev_key = None
        #self._editor._onechar = False
        self._init_properties ()
        self._update_ui ()

    def do_destroy(self):
        self.reset ()
        self.do_focus_out ()
        #self.db.sync_usrdb ()
        super(EngineTable, self).destroy()

    def _init_properties(self):
        self.properties= IBus.PropList ()
        self._status_property = IBus.Property(key=u'status',
                                              label=None,
                                              icon=None,
                                              tooltip=None,
                                              sensitive=True,
                                              visible=True)
        self.properties.append(self._status_property)
        if self.db._is_chinese:
            self._cmode_property = IBus.Property(key=u'cmode',
                                                 label=None,
                                                 icon=None,
                                                 tooltip=None,
                                                 sensitive=True,
                                                 visible=True)
            self.properties.append(self._cmode_property)
        self._letter_property = IBus.Property(key=u'letter',
                                              label=None,
                                              icon=None,
                                              tooltip=None,
                                              sensitive=True,
                                              visible=True)
        self.properties.append(self._letter_property)
        self._punct_property = IBus.Property(key=u'punct',
                                              label=None,
                                              icon=None,
                                              tooltip=None,
                                             sensitive=True,
                                             visible=True)
        self.properties.append(self._punct_property)
        self._py_property = IBus.Property(key=u'py_mode',
                                          label=None,
                                          icon=None,
                                          tooltip=None,
                                          sensitive=True,
                                          visible=True)
        self.properties.append(self._py_property)
        self._onechar_property = IBus.Property(key=u'onechar',
                                               label=None,
                                               icon=None,
                                               tooltip=None,
                                               sensitive=True,
                                               visible=True)
        self.properties.append(self._onechar_property)
        self._auto_commit_property = IBus.Property(key=u'acommit',
                                                   label=None,
                                                   icon=None,
                                                   tooltip=None,
                                                   sensitive=True,
                                                   visible=True)
        self.properties.append(self._auto_commit_property)
        self.register_properties (self.properties)
        self._refresh_properties ()

    def _refresh_properties(self):
        '''Method used to update properties'''
        # taken and modified from PinYin.py :)
        if self._mode == 1: # refresh mode
            if self._status == u'CN':
                self._set_property(self._status_property,
                                   'chinese.svg',
                                   _('Chinese Mode'),
                                   _('Switch to English mode'))
            else:
                self._set_property(self._status_property,
                                   'ibus-table.svg',
                                   self._status,
                                   _('Switch to English mode'))
        else:
            self._set_property(self._status_property,
                               'english.svg',
                               _('English Mode'),
                               _('Switch to Table mode'))
        self.update_property(self._status_property)

        if self._full_width_letter[self._mode]:
            self._set_property(self._letter_property,
                               'full-letter.svg',
                               _('Full Letter'),
                               _('Switch to half-width letter'))
        else:
            self._set_property(self._letter_property,
                               'half-letter.svg',
                               _('Half Letter'),
                               _('Switch to full-width letter'))
        self.update_property(self._letter_property)

        if self._full_width_punct[self._mode]:
            self._set_property(self._punct_property,
                               'full-punct.svg',
                               _('Full-width Punctuation'),
                               _('Switch to half-width punctuation'))
        else:
            self._set_property(self._punct_property,
                               'half-punct.svg',
                               _('Half-width Punctuation'),
                               _('Switch to full-width punctuation'))
        self.update_property(self._punct_property)

        if self._editor._py_mode:
            self._set_property(self._py_property,
                               'py-mode.svg',
                               _('PinYin Mode'),
                               _('Switch to Table mode'))
        else:
            self._set_property(self._py_property,
                               'tab-mode.svg',
                               _('Table Mode'),
                               _('Switch to PinYin mode'))
        self.update_property(self._py_property)

        if self._editor._onechar:
            self._set_property(self._onechar_property,
                               'onechar.svg',
                               _('Single Char Mode'),
                               _('Switch to phrase mode'))
        else:
            self._set_property(self._onechar_property,
                               'phrase.svg',
                               _('Phrase Mode'),
                               _('Switch to single char mode'))
        self.update_property(self._onechar_property)

        if self._auto_commit:
            self._set_property(
                self._auto_commit_property,
                'acommit.svg',
                _('Direct Commit Mode'),
                _('Switch to normal commit mode, which use space to commit')
            )
        else:
            self._set_property(self._auto_commit_property,
                               'ncommit.svg',
                               _('Normal Commit Mode'),
                               _('Switch to direct commit mode'))
        self.update_property(self._auto_commit_property)

        # the chinese_mode:
        if self.db._is_chinese:
            if self._editor._chinese_mode == 0:
                self._set_property(self._cmode_property,
                                   'sc-mode.svg',
                                   _('Simplified Chinese Mode'),
                                   _('Switch to Traditional Chinese mode'))
            elif self._editor._chinese_mode == 1:
                self._set_property(
                    self._cmode_property,
                    'tc-mode.svg',
                    _('Traditional Chinese Mode'),
                    _('Switch to Simplify Chinese first Big Charset Mode')
                )
            elif self._editor._chinese_mode == 2:
                self._set_property(
                    self._cmode_property,
                    'scb-mode.svg',
                    _('Simplified Chinese First Big Charset Mode'),
                    _('Switch to Traditional Chinese first Big Charset Mode')
                )
            elif self._editor._chinese_mode == 3:
                self._set_property(
                    self._cmode_property,
                    'tcb-mode.svg',
                    _('Traditional Chinese First Big Charset Mode'),
                    _('Switch to Big Charset Mode')
                )
            elif self._editor._chinese_mode == 4:
                self._set_property(
                    self._cmode_property,
                    'cb-mode.svg',
                    _('Big Chinese Mode'),
                    _('Switch to Simplified Chinese Mode')
                )
        self.update_property(self._cmode_property)

    def _set_property(self, property, icon, label, tooltip):
        property.set_icon(u'%s%s' %(self._icon_dir, icon))
        property.set_label(IBus.Text.new_from_string(unicode(label)))
        property.set_tooltip(IBus.Text.new_from_string(unicode(tooltip)))

    def _change_mode(self):
        '''Shift input mode, TAB -> EN -> TAB
        '''
        self._mode = int(not self._mode)
        self.reset()
        self._update_ui()

    def do_property_activate(self,
                             property,
                             prop_state=IBus.PropState.UNCHECKED):
        '''Shift property'''
        if property == u"status":
            self._change_mode()
        elif property == u'py_mode' and self._ime_py:
            self._editor.r_shift()
        elif property == u'onechar':
            self._editor._onechar = not self._editor._onechar
            self._config.set_value(
                self._config_section,
                "OneChar",
                GLib.Variant.new_boolean(self._editor._onechar)
           )

        elif property == u'acommit':
            self._auto_commit = not self._auto_commit
            self._config.set_value(self._config_section,
                                   "AutoCommit",
                                   GLib.Variant.new_boolean(self._auto_commit)
           )

        elif property == u'letter':
            self._full_width_letter[self._mode] = not self._full_width_letter[self._mode]
            if self._mode:
                self._config.set_value(
                    self._config_section,
                    "TabDefFullWidthLetter",
                    GLib.Variant.new_boolean(self._full_width_letter[self._mode])
                )
            else:
                self._config.set_value(
                    self._config_section,
                    "EnDefFullWidthLetter",
                    GLib.Variant.new_boolean(self._full_width_letter[self._mode])
               )

        elif property == u'punct':
            self._full_width_punct[self._mode] = not self._full_width_punct[self._mode]
            if self._mode:
                self._config.set_value(
                    self._config_section,
                    "TabDefFullWidthPunct",
                    GLib.Variant.new_boolean(self._full_width_punct[self._mode])
               )
            else:
                self._config.set_value(
                    self._config_section,
                    "EnDefFullWidthPunct",
                    GLib.Variant.new_boolean(self._full_width_punct[self._mode])
               )
        elif property == u'cmode':
            self._editor.change_chinese_mode()
            self.reset()
        self._refresh_properties()

    def _update_preedit (self):
        '''Update Preedit String in UI'''
        _str = self._editor.get_preedit_strings()
        if _str == u'':
            super(EngineTable, self).update_preedit_text(IBus.Text.new_from_string(u''), 0, False)
        else:
            attrs = IBus.AttrList()
            res = patt_edit.match(_str)
            if res:
                _str = u''
                ures = patt_uncommit.match(res.group(1))
                if ures:
                    _str=u''.join(ures.groups())
                    lc = len(ures.group(1))
                    lu = len(ures.group(2))
                    attrs.append(IBus.attr_foreground_new(0xff1b3f03, 0, lc))
                    attrs.append(IBus.attr_foreground_new(0xff0895a2, lc, lu))
                    lg1 = len(_str)
                else:
                    _str += res.group(1)
                    lg1 = len(res.group(1))
                    attrs.append(IBus.attr_foreground_new(0xff1b3f03, 0, lg1))
                _str += res.group(2)
                _str += res.group(3)
                lg2 = len(res.group(2))
                lg3 = len(res.group(3))
                attrs.append(IBus.attr_foreground_new(0xff0e0ea0, lg1, lg2))
                attrs.append(IBus.attr_foreground_new(0xff1b3f03, lg1+lg2, lg3))
            else:
                attrs.append(IBus.attr_foreground_new(0xff1b3f03, 0, len(_str)))
            # because IBus now can only insert preedit into txt, so...
            # attrs = IBus.AttrList()
            attrs.append(IBus.attr_underline_new(IBus.AttrUnderline.SINGLE, 0, len(_str)))
            text = IBus.Text.new_from_string(_str)
            text.set_attributes(attrs)
            super(EngineTable, self).update_preedit_text(text, self._editor.get_caret(), True)


    def _update_aux (self):
        '''Update Aux String in UI'''
        _ic = self._editor.get_aux_strings()
        if _ic:
            text = IBus.Text.new_from_string(_ic)
            attr = IBus.attr_foreground_new(0xff9515b5, 0, len(_ic))
            text.append_attribute(attr.get_attr_type(),
                                  attr.get_value(),
                                  attr.get_start_index(),
                                  attr.get_end_index())
            #attrs = [ scim.Attribute(0,len(_ic),scim.ATTR_FOREGROUND,0x5540c1)]

            super(EngineTable, self).update_auxiliary_text(text, True)
        else:
            self.hide_auxiliary_text()
            #self.update_aux_string(u'', None, False)



    def _update_lookup_table(self):
        '''Update Lookup Table in UI'''
        if self._editor.is_empty():
            self.hide_lookup_table()
            return
        self.update_lookup_table(self._editor.get_lookup_table(), True)

    def _update_ui (self):
        '''Update User Interface'''
        self._update_lookup_table ()
        self._update_preedit ()
        self._update_aux ()

    #def add_string_len(self, astring):
    #    if self._sm_on:
    #        try:
    #            self._sm.Accumulate(len(astring))
    #        except:
    #            pass

    def commit_string (self,string):
        self._editor.clear()
        self._update_ui()
        super(EngineTable,self).commit_text(IBus.Text.new_from_string(string))
        self._prev_char = string[-1]

    def _convert_to_full_width (self, c):
        '''convert half width character to full width'''
        if c in [u".", u"\\", u"^", u"_", u"$", u"\"", u"'", u">", u"<" ]:
            if c == u".":
                if self._prev_char and self._prev_char.isdigit () \
                    and self._prev_key and chr (self._prev_key.code) == self._prev_char:
                    return u"."
                else:
                    return u"\u3002"
            elif c == u"\\":
                return u"\u3001"
            elif c == u"^":
                return u"\u2026\u2026"
            elif c == u"_":
                return u"\u2014\u2014"
            elif c == u"$":
                return u"\uffe5"
            elif c == u"\"":
                self._double_quotation_state = not self._double_quotation_state
                if self._double_quotation_state:
                    return u"\u201c"
                else:
                    return u"\u201d"
            elif c == u"'":
                self._single_quotation_state = not self._single_quotation_state
                if self._single_quotation_state:
                    return u"\u2018"
                else:
                    return u"\u2019"
            elif c == u"<":
                if self._mode:
                    return u"\u300a"
            elif c == u">":
                if self._mode:
                    return u"\u300b"

        return unichar_half_to_full(c)

    def _match_hotkey (self, key, code, mask):

        if key.code == code and key.mask == mask:
            if self._prev_key and key.code == self._prev_key.code and key.mask & IBus.ModifierType.RELEASE_MASK:
                return True
            if not key.mask & IBus.ModifierType.RELEASE_MASK:
                return True

        return False

    def do_process_key_event(self, keyval, keycode, state):
        '''Process Key Events
        Key Events include Key Press and Key Release,
        IBus.ModifierType means Key Pressed
        '''
        key = KeyEvent(keyval, state & IBus.ModifierType.RELEASE_MASK == 0, state)
        # ignore NumLock mask
        key.mask &= ~IBus.ModifierType.MOD2_MASK

        result = self._process_key_event(key)
        self._prev_key = key
        return result

    def _process_key_event(self, key):
        '''Internal method to process key event'''
        # Match mode switch hotkey
        if not self._editor._t_chars and (self._match_hotkey(key, IBus.KEY_Shift_L, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK)):
            self._change_mode()
            return True

        # Match full half letter mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_space, IBus.ModifierType.SHIFT_MASK):
            self.do_property_activate("letter")
            return True

        # Match full half punct mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_period, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate("punct")
            return True

        # we ignore all hotkeys
#        if key.mask & IBus.ModifierType.MOD1_MASK:
#            return False

        # Ignore key release event
#        if key.mask & IBus.ModifierType.RELEASE_MASK:
#            return True

        if self._mode:
            return self._table_mode_process_key_event(key)
        else:
            return self._english_mode_process_key_event(key)

    def _english_mode_process_key_event (self, key):
        '''English Mode Process Key Event'''
        # Ignore key release event
        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True

        if key.code >= 128:
            return False
        # we ignore all hotkeys here
        if key.mask & (IBus.ModifierType.CONTROL_MASK |
                IBus.ModifierType.MOD1_MASK):
            return False

        keychar = unichr(key.code)
        if ispunct(key.code): # if key code is a punctation
            if self._full_width_punct[self._mode]:
                self.commit_string (self._convert_to_full_width (keychar))
                return True
            else:
                self.commit_string (keychar)
                return True

        # then, the key code is a letter or digit
        if self._full_width_letter[self._mode]:
            # in full width letter mode
            self.commit_string (self._convert_to_full_width (keychar))
            return True
        else:
            return False

        # should not reach there
        return False

    def _table_mode_process_key_event (self, key):
        '''Xingma Mode Process Key Event'''
        cond_letter_translate = lambda (c): \
            self._convert_to_full_width (c) if self._full_width_letter [self._mode] else c
        cond_punct_translate = lambda (c): \
            self._convert_to_full_width (c) if self._full_width_punct [self._mode] else c

        # We have to process the pinyin mode change key event here,
        # because we ignore all Release event below.
        if self._match_hotkey (key, IBus.KEY_Shift_R, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK) and self._ime_py:
            res = self._editor.r_shift ()
            self._refresh_properties ()
            self._update_ui ()
            return res
        # process commit to preedit
        if self._match_hotkey(key, IBus.KEY_Shift_R, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK) or self._match_hotkey(key, IBus.KEY_Shift_L, IBus.ModifierType.SHIFT_MASK | IBus.ModifierType.RELEASE_MASK):
            res = self._editor.l_shift ()
            self._update_ui ()
            return res

        # Match single char mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_comma, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"onechar" )
            return True
        # Match direct commit mode switch hotkey
        if self._match_hotkey(key, IBus.KEY_slash, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"acommit" )
            return True

        # Match Chinese mode shift
        if self._match_hotkey (key, IBus.KEY_semicolon, IBus.ModifierType.CONTROL_MASK):
            self.do_property_activate ( u"cmode" )
            return True

        # Match speedmeter shift
        #if self._match_hotkey (key, IBus.KEY_apostrophe, IBus.ModifierType.CONTROL_MASK):
        #    self._sm_on = not self._sm_on
        #    if self._sm_on:
        #        self._sm.Show ()
        #    else:
        #        self._sm.Hide ()
        #    return True
        # Ignore key release event now :)
        if key.mask & IBus.ModifierType.RELEASE_MASK:
            return True

        #
        keychar = unichr (key.code)

        if self._editor.is_empty ():
            # we have not input anything
            if key.code >= 32 and key.code <= 127 and ( keychar not in self._valid_input_chars ) \
                    and (not key.mask & IBus.ModifierType.MOD1_MASK | IBus.ModifierType.CONTROL_MASK):
                if key.code == IBus.KEY_space:
                    #self.commit_string (cond_letter_translate (keychar))
                    # little hack to make ibus to input space in gvim :)
                    if self._full_width_letter [self._mode]:
                        self.commit_string (cond_letter_translate (keychar))
                        return True
                    else:
                        return False
                if ispunct(key.code):
                    self.commit_string (cond_punct_translate (keychar))
                    return True
                if isdigit(key.code):
                    self.commit_string (cond_letter_translate (keychar))
                    return True
            elif (key.code < 32 or key.code > 127) and ( keychar not in self._valid_input_chars ) \
                    and(not self._editor._py_mode):
                return False

        if key.code == IBus.KEY_Escape:
            self.reset ()
            self._update_ui ()
            return True

        elif key.code in (IBus.KEY_Return, IBus.KEY_KP_Enter):
            commit_string = self._editor.get_all_input_strings ()
            self.commit_string (commit_string)
            return True

        elif key.code in (IBus.KEY_Down, IBus.KEY_KP_Down) :
            res = self._editor.arrow_down ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Up, IBus.KEY_KP_Up):
            res = self._editor.arrow_up ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Left, IBus.KEY_KP_Left) and key.mask & IBus.ModifierType.CONTROL_MASK:
            res = self._editor.control_arrow_left ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Right, IBus.KEY_KP_Right) and key.mask & IBus.ModifierType.CONTROL_MASK:
            res = self._editor.control_arrow_right ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Left, IBus.KEY_KP_Left):
            res = self._editor.arrow_left ()
            self._update_ui ()
            return res

        elif key.code in (IBus.KEY_Right, IBus.KEY_KP_Right):
            res = self._editor.arrow_right ()
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_BackSpace and key.mask & IBus.ModifierType.CONTROL_MASK:
            res = self._editor.control_backspace ()
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_BackSpace:
            res = self._editor.backspace ()
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_Delete and key.mask & IBus.ModifierType.CONTROL_MASK:
            res = self._editor.control_delete ()
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_Delete:
            res = self._editor.delete ()
            self._update_ui ()
            return res

        elif key.code >= IBus.KEY_1 and key.code <= IBus.KEY_9 and self._editor._candidates[0] and key.mask & IBus.ModifierType.CONTROL_MASK:
            res = self._editor.number (key.code - IBus.KEY_1)
            self._update_ui ()
            return res

        elif key.code >= IBus.KEY_1 and key.code <= IBus.KEY_9 and self._editor._candidates[0] and key.mask & IBus.ModifierType.MOD1_MASK:
            res = self._editor.alt_number (key.code - IBus.KEY_1)
            self._update_ui ()
            return res

        elif key.code == IBus.KEY_space:
            o_py = self._editor._py_mode
            sp_res = self._editor.space ()
            #return (KeyProcessResult,whethercommit,commitstring)
            if sp_res[0]:
                if self._auto_select:
                    self.commit_string ("%s " %sp_res[1])
                else:
                    self.commit_string (sp_res[1])
                #self.add_string_len(sp_res[1])
                self.db.check_phrase (sp_res[1], sp_res[2])
            else:
                if sp_res[1] == u' ':
                    self.commit_string (cond_letter_translate (u" "))
            if o_py != self._editor._py_mode:
                self._refresh_properties ()
                self._update_ui ()
            return True
        # now we ignore all else hotkeys
        elif key.mask & (IBus.ModifierType.CONTROL_MASK |
                IBus.ModifierType.MOD1_MASK):
            return False

        elif key.mask & IBus.ModifierType.MOD1_MASK:
            return False

        elif keychar in self._valid_input_chars or \
                ( self._editor._py_mode and \
                    keychar in u'abcdefghijklmnopqrstuvwxyz!@#$%' ):
            if self._auto_commit and ( len(self._editor._chars[0]) == self._ml \
                    or len (self._editor._chars[0]) in self.db.pkeylens )\
                    and not self._editor._py_mode:
                # it is time to direct commit
                sp_res = self._editor.space ()
                #return (whethercommit,commitstring)
                if sp_res[0]:
                    self.commit_string (sp_res[1])
                    #self.add_string_len(sp_res[1])
                    self.db.check_phrase (sp_res[1],sp_res[2])

            res = self._editor.add_input( keychar )
            if not res:
                if ispunct(key.code):
                    key_char = cond_punct_translate (keychar)
                else:
                    key_char = cond_letter_translate (keychar)
                sp_res = self._editor.space ()
                #return (KeyProcessResult,whethercommit,commitstring)
                if sp_res[0]:
                    self.commit_string (sp_res[1] + key_char)
                    #self.add_string_len(sp_res[1])
                    self.db.check_phrase (sp_res[1],sp_res[2])
                    return True
                else:
                    self.commit_string ( key_char )
                    return True
            else:
                if self._auto_commit and self._editor.one_candidate () and \
                        (len(self._editor._chars[0]) == self._ml \
                            or not self.db._is_chinese):
                    # it is time to direct commit
                    sp_res = self._editor.space ()
                    #return (whethercommit,commitstring)
                    if sp_res[0]:
                        self.commit_string (sp_res[1])
                        #self.add_string_len(sp_res[1])
                        self.db.check_phrase (sp_res[1], sp_res[2])
                        return True
            self._update_ui ()
            return True

        elif key.code in self._page_down_keys \
                and self._editor._candidates[0]:
            res = self._editor.page_down()
            self._update_lookup_table ()
            return res

        elif key.code in self._page_up_keys \
                and self._editor._candidates[0]:
            res = self._editor.page_up ()
            self._update_lookup_table ()
            return res

        elif key.code >= IBus.KEY_1 and key.code <= IBus.KEY_9 and self._editor._candidates[0]:
            input_keys = self._editor.get_all_input_strings ()
            res = self._editor.number (key.code - IBus.KEY_1)
            if res:
                o_py = self._editor._py_mode
                commit_string = self._editor.get_preedit_strings ()
                self.commit_string (commit_string)
                #self.add_string_len(commit_string)
                if o_py != self._editor._py_mode:
                    self._refresh_properties ()
                    self._update_ui ()
                # modify freq info
                self.db.check_phrase (commit_string, input_keys)
            return True

        elif key.code <= 127:
            if not self._editor._candidates[0]:
                commit_string = self._editor.get_all_input_strings ()
            else:
                self._editor.commit_to_preedit ()
                commit_string = self._editor.get_preedit_strings ()
            # we need to take care of the py_mode here :)
            py_mode = self._editor._py_mode
            self._editor.clear ()
            if py_mode:
                self._refresh_properties ()
            if ispunct(key.code):
                self.commit_string(commit_string + cond_punct_translate(keychar))
            else:
                self.commit_string(commit_string + cond_letter_translate(keychar))

            return True
        return False

    # below for initial test
    def do_focus_in(self):
        if self._on:
            self.register_properties (self.properties)
            self._refresh_properties ()
            self._update_ui ()
            #try:
            #    if self._sm_on:
            #        self._sm.Show ()
            #    else:
            #        self._sm.Hide ()
            #except:
            #    pass

    def do_focus_out(self):
        #try:
        #    self._sm.Hide()
        #except:
        #    pass
        pass

    def do_enable(self):
        #try:
        #    self._sm.Reset()
        #except:
        #    pass
        self._on = True
        self.do_focus_in()

    def do_disable(self):
        self.reset()
        #try:
        #    self._sm.Hide()
        #except:
        #    pass
        self._on = False


    def do_page_up(self):
        if self._editor.page_up():
            self._update_lookup_table()
            return True
        return True

    def do_page_down(self):
        if self._editor.page_down():
            self._update_lookup_table()
            return True
        return False

    def config_value_changed_cb(self, config, section, name, value):
        value = variant_to_value(value)
        if section == self._config_section:
            if name == u'AutoCommit':
                self._auto_commit = value
            elif name == u'ChineseMode':
                self._editor._chinese_mode = value
            elif name == u'EnDefFullWidthLetter':
                self._full_width_letter[0] = value
            elif name == u'EnDefFullWidthPunct':
                self._full_width_punct[0] = value
            elif name == u'LookupTableOrientation':
                self._editor._lookup_table.set_orientation (value)
            elif name == u'LookupTableSelectKeys':
                self._editor.set_select_keys (value)
            elif name == u'OneChar':
                self._editor._onechar = value
            elif name == u'TabDefFullWidthLetter':
                self._full_width_letter[1] = value
            elif name == u'TabDefFullWidthPunct':
                self._full_width_punct[1] = value

    # for further implementation :)
    @classmethod
    def CONFIG_VALUE_CHANGED(cls, bus, section, name, value):
        config = bus.get_config()
        if section != self._config_section:
            return

    @classmethod
    def CONFIG_RELOADED(cls, bus):
        config = bus.get_config()
        if section != self._config_section:
            return
