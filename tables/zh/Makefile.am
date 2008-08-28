# vim:set noet ts=4:
#
# ibus-table
#
# Copyright (c) 2007-2008 Yu Yuwei <acevery@gmail.com>
#
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA  02111-1307  USA
#
# $Id: $
#

createdb = \
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py -o -p $(abs_top_srcdir)/data/pinyin_table.txt.bz2 -k $(datadir) -b $(bindir)

if IBUS_TABLE_EXTRA_PHRASES
createdb += -e $(srcdir)/extra_phrase.txt
endif

createdb_index = \
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py -i

extra_tables_DATA = extra_phrase.txt 

tables_DATA = 
if IBUS_TABLE_BUILD_ZHENGMA
tables_DATA += zhengma.db zhengma.engine
endif

if IBUS_TABLE_BUILD_WUBI86
tables_DATA += wubi86.db wubi86.engine
endif

if IBUS_TABLE_BUILD_WUBI98
tables_DATA += wubi98.db wubi98.engine
endif

if IBUS_TABLE_BUILD_CANGJIE5
tables_DATA += cangjie5.db cangjie5.engine
endif

if IBUS_TABLE_BUILD_ERBI_QS
tables_DATA += erbi-qs.db erbi-qs.engine
endif

tables_DATA += $(NULL)

tablesdir = $(pkgdatadir)/tables
extra_tablesdir = $(pkgdatadir)/tables

EXTRA_DIST = \
	zhengma.txt \
	wubi86.txt \
	wubi98.txt \
	cangjie5.txt \
	erbi-qs.txt \
	extra_phrase.txt \
	$(NULL)

DISTCLEANFILES = \
	*.db \
	$(NULL)

%.txt %.engine: %.db
	$(createdb) -n %.db -s %.txt

install-data-hook:
	@(if test x"$$NO_INDEX" = x""; then \
		cd $(DESTDIR)$(tablesdir); \
		for db in ${tables_DATA}; do \
		echo "Create Index for $$db"; \
			$(createdb_index) -n $$db; \
		done \
	fi)
