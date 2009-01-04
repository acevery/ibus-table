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
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py \
		-k $(datadir) \
		-b $(bindir)

createdb_index = \
	$(PYTHON) $(abs_top_srcdir)/engine/tabcreatedb.py -i

tables_DATA =
engine_DATA =

if IBUS_TABLE_BUILD_ADDITIONAL
tables_DATA += compose.db
engine_DATA += compose.engine
endif

tables_DATA += $(NULL)
engine_DATA += $(NULL)


tablesdir = $(pkgdatadir)/tables
enginedir = $(datadir)/ibus/engine

EXTRA_DIST = \
	compose.txt \
	$(NULL)

DISTCLEANFILES = \
	*.db \
	*.engine \
	$(NULL)

CLEANFILES = \
	$(DISTCLEANFILES) \
	$(NULL)

MAINTAINERCLEANFILES = \
	Makefile.in \
	$(NULL)

.db.engine:
	@echo "$@ is done :)"

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
