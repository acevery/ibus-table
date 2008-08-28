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
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py -o -p $(abs_top_srcdir)/data/pinyin_table.txt.bz2 -k $(abs_top_srcdir)

if IBUS_TABLE_EXTRA_PHRASES
$(createdb) += -e $(srcdir)/extra_phrase.txt
endif

createdb_index = \
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py -i

tables_DATA = extra_phrase.txt 

if IBUS_TABLE_BUILD_ZHENGMA
$(table_DATA) += zhengma.db
endif

if IBUS_TABLE_BUILD_WUBI86
$(table_DATA) += wubi86.db
endif

if IBUS_TABLE_BUILD_WUBI98
$(table_DATA) += wubi98.db
endif

if IBUS_TABLE_BUILD_CANGJIE5
$(table_DATA) += cangjie5.db
endif

if IBUS_TABLE_BUILD_ERBI_QS
$(table_DATA) += erbi-qs.db
endif

$(table_DATA) += $(NULL)

tablesdir = $(pkgdatadir)/tables

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

.txt.db:
	$(createdb) -n $@ -s $<

install-data-hook:
	@(if test x"$$NO_INDEX" = x""; then \
		cd $(DESTDIR)$(tablesdir); \
		for db in ${tables_DATA}; do \
		echo "Create Index for $$db"; \
			$(createdb_index) -n $$db; \
		done \
	fi)
