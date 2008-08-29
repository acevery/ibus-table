# vim:set et ts=4:
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

# if not 1, append datestamp to the version number.
m4_define([package_name], [ibus-table])
m4_define([ibus_released], [0])
m4_define([ibus_major_version], [0])
m4_define([ibus_minor_version], [1])
m4_define([ibus_micro_version], [1])
m4_define(ibus_maybe_datestamp,
    m4_esyscmd([if test x]ibus_released[ != x1; then date +.%Y%m%d | tr -d '\n\r'; fi]))

m4_define([ibus_version],
    ibus_major_version.ibus_minor_version.ibus_micro_version[]ibus_maybe_datestamp)

AC_INIT([package_name], [ibus_version], [http://code.google.com/p/ibus/issues/entry], [package_name])
AM_INIT_AUTOMAKE([1.10])
# AC_GNU_SOURCE

# AC_CONFIG_HEADERS([config.h])
AC_CONFIG_MACRO_DIR([m4])

# define PACKAGE_VERSION_* variables
# AS_VERSION
# AS_NANO
# AM_SANITY_CHECK
# AM_MAINTAINER_MODE
# AM_DISABLE_STATIC
# AC_PROG_CC
# AM_PROG_CC_C_O
# AC_PROG_CXX
# AC_ISC_POSIX
# AC_HEADER_STDC
# AM_PROG_LIBTOOL

#check python
AM_PATH_PYTHON([2.5])

# define GETTEXT_* variables
GETTEXT_PACKAGE=ibus-table
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [Define to the read-only architecture-independent data directory.])

AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_VERSION(0.16.1)


# ARGUMENTS
AC_ARG_ENABLE([zhengma],
	[AC_HELP_STRING([--enable-zhengma],
		[Generate ZhengMa Engine])], ,
	[enable_zhengma=no])

AM_CONDITIONAL([IBUS_TABLE_BUILD_ZHENGMA],[test x"$enable_zhengma" = x"yes"])

AC_ARG_ENABLE([wubi86],
	[AC_HELP_STRING([--enable-wubi86],
		[Generate WuBi86 Engine])], ,
	[enable_wubi86=no])

AM_CONDITIONAL([IBUS_TABLE_BUILD_WUBI86],[test x"$enable_wubi86" = x"yes"])

AC_ARG_ENABLE([wubi98],
	[AC_HELP_STRING([--enable-wubi98],
		[Generate WuBi98 Engine])], ,
	[enable_wubi98=no])

AM_CONDITIONAL([IBUS_TABLE_BUILD_WUBI98],[test x"$enable_wubi98" = x"yes"])

AC_ARG_ENABLE([cangjie5],
	[AC_HELP_STRING([--enable-cangjie5],
		[Generate CangJie5 Engine])], ,
	[enable_cangjie5=no])

AM_CONDITIONAL([IBUS_TABLE_BUILD_CANGJIE5],[test x"$enable_cangjie5" = x"yes"])

AC_ARG_ENABLE([erbi-qs],
	[AC_HELP_STRING([--enable-erbi-qs],
		[Generate ErBi-QS Engine])], ,
	[enable_erbi_qs=no])

AM_CONDITIONAL([IBUS_TABLE_BUILD_ERBI_QS],[test x"$enable_erbi_qs" = x"yes"])

AC_ARG_ENABLE([extra-phrases],
	[AC_HELP_STRING([--enable-extra-phrases],
		[Add extra phrases into builded Engine])], ,
	[enable_extra_phrases=no])

AM_CONDITIONAL([IBUS_TABLE_EXTRA_PHRASES],[test x"$enable_extra_phrases" = x"yes"])

AC_ARG_ENABLE([additional],
	[AC_HELP_STRING([--disable-additional],
		[Don't generate additional Engine])], ,
	[enable_aditional=yes])

AM_CONDITIONAL([IBUS_TABLE_BUILD_ADDITIONAL],[test x"$enable_erbi_qs"=x"yes"])

# OUTPUT files
AC_CONFIG_FILES(po/Makefile.in
Makefile
ibus-table.spec
engine/Makefile
engine/ibus-engine-table
engine/ibus-table-createdb
data/Makefile
doc/Makefile
doc/table.engine
icons/Makefile
icons/zh/Makefile
icons/additional/Makefile
tables/Makefile
tables/zh/Makefile
tables/additional/Makefile
m4/Makefile
)

AC_OUTPUT

AC_MSG_RESULT([
Build options:
  Version					$VERSION
  Install prefix			$prefix
  Build ZhengMa				$enable_zhengma
  Build WuBi98				$enable_wubi98
  Build WuBi86				$enable_wubi86
  Build CangJie5			$enable_cangjie5
  Build ErBi-QS				$enable_erbi-qs
  Build Additional			$enable_additional
  Integrate Extra Phrases	$enable_extra_phrases
])
