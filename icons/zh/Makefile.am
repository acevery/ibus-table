# vim:set noet ts=4:
#
# ibus-pinyin - The PinYin engine for IBus
#
# Copyright (c) 2007-2008 Huang Peng <shawn.p.huang@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


icons_DATA = 

if IBUS_TABLE_BUILD_ZHENGMA
$(icons_DATA) += zhengma.svg
endif

if IBUS_TABLE_BUILD_WUBI86
$(icons_DATA) += wubi86.svg
endif

if IBUS_TABLE_BUILD_WUBI98
$(icons_DATA) += wubi98.svg
endif

if IBUS_TABLE_BUILD_CANGJIE5
$(icons_DATA) += cangjie5.svg
endif

if IBUS_TABLE_BUILD_ERBI_QS
$(icons_DATA) += erbi-qs.svg
endif

$(icons_DATA) += $(NULL)

iconsdir = $(pkgdatadir)/icons

EXTRA_DIST = \
	zhengma.svg \
	wubi86.svg \
	wubi98.svg \
	cangjie5.svg \
	erbi-qs.svg \
	$(NULL)
