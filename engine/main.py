# vim:set et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
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

import os
import sys
import optparse
import ibus
import gobject
import factory
try:
    db_dir = os.path.join (os.getenv('IBUS_TABLE_LOCATION'),'tables')
except:
    db_dir = "/usr/share/ibus-table/tables"

opt = optparse.OptionParser()

opt.set_usage ('%prog --table a_table.db')
opt.add_option('--table', '-t',
        action = 'store',type = 'string',dest = 'db',default = '',
        help = 'Set the IME table file, default: %default')
opt.add_option('--daemon','-d',
        action = 'store_true',dest = 'daemon',default=False,
        help = 'Run as daemon, default: %default')
opt.add_option('--ibus', '-i',
        action = 'store_true',dest = 'ibus',default = False,
        help = 'Set the IME icon file, default: %default')


(options, args) = opt.parse_args()
#if not options.db:
#    opt.error('no db found!')


class IMApp:
    def __init__(self, dbfile,exec_by_ibus):
        self.__mainloop = gobject.MainLoop()
        self.__bus = ibus.Bus()
        self.__bus.connect("destroy", self.__bus_destroy_cb)
        if exec_by_ibus:
            self.__bus.request_name("org.freedesktop.IBus.Table", 0)
        else:
            self.__component = ibus.Component("org.freedesktop.IBus.Table",
                                              "Table Component",
                                              "0.1.0",
                                              "GPL",
                                              "Yuwei Yu <acevery@gmail.com>")
            self.__factory = factory.EngineFactory(self.__bus, dbfile)
            # now we get IME info from self.__factory.db
            name = self.__factory.db.get_ime_property ("name")
            longname = name
            description = self.__factory.db.get_ime_property ("description")
            language = self.__factory.db.get_ime_property ("languages")
            license = self.__factory.db.get_ime_property ("credit")
            author = self.__factory.db.get_ime_property ("author")
            icon = self.__factory.db.get_ime_property ("icon")
            if icon:
                try:
                    icon_dir = os.path.join (os.getenv('IBUS_TABLE_LOCATION'),
                            'icons')
                except:
                    icon_dir = "/usr/share/ibus-table/icons"
                icon = os.path.join (icon_dir, icon)
                if not os.access( icon, os.F_OK):
                    icon = ''
            layout = self.__factory.db.get_ime_property ("layout")
            
            self.__component.add_engine(name,
                                        longname,
                                        description,
                                        language,
                                        license,
                                        author,
                                        icon,
                                        layout)
            self.__bus.register_component(self.__component)


    def run(self):
        self.__mainloop.run()

    def quit(self):
        self.__bus_destroy_cb()

    def __bus_destroy_cb(self, bus=None):
        try:
            self.__factory.do_destroy()
        except:
            pass
        self.__mainloop.quit()


def main():
    if options.daemon :
        if os.fork():
                sys.exit()
    if os.access( options.db, os.F_OK):
        db = options.db
    else:
        db = '%s%s%s' % (db_dir,os.path.sep, os.path.basename(options.db) )
    ima=IMApp(db, options.ibus)
    try:
        ima.run()
    except KeyboardInterrupt:
        ima.quit()

if __name__ == "__main__":
    main()

