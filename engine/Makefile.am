# vim:set noet ts=4:
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2008 Yu Yuwei <acevery@gmail.com>
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

engine_table_PYTHON = \
	factory.py \
	main.py \
	table.py \
	tabcreatedb.py \
	tabdict.py \
	tabsqlitedb.py \
	$(NULL)
engine_table_DATA = \
	$(NULL)
engine_tabledir = $(datadir)/ibus-table/engine

bin_SCRIPTS = ibus-engine-table \
			  table-createdb \
			  $(NULL)


EXTRA_DIST = \
	table-createdb.in \
	ibus-engine-table.in \
	$(NULL)

CLEANFILES = \
	*.pyc \
	py.db \
	$(NULL)

test:
	$(ENV) \
		IBUS_TABLE_LOCATION=$(abs_top_srcdir) \
		DBUS_DEBUG=true \
		LANG=en_US \
		PYTHONPATH=$(abs_top_srcdir) \
		$(PYTHON) $(srcdir)/main.py

