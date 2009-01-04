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
opt.add_option('--icon', '-i',
        action = 'store',type = 'string',dest = 'icon',default = '',
        help = 'Set the IME icon file, default: %default')


(options, args) = opt.parse_args()
if not options.db:
    opt.error('no db found!')

class IMApp:
    def __init__(self, dbfile, iconfile=''):
        self.__mainloop = gobject.MainLoop()
        self.__bus = ibus.Bus()
        self.__bus.connect("destroy", self.__bus_destroy_cb)
        self.__engine = factory.EngineFactory(self.__bus, dbfile,\
                iconfile)
        self.__engine.register()

    def run(self):
        self.__mainloop.run()

    def quit(self):
        self.__bus_destroy_cb()

    def __bus_destroy_cb(self, bus=None):
        self.__engine.do_destroy()
        self.__mainloop.quit()


def main():
    if options.daemon :
        if os.fork():
                sys.exit()
    if os.access( options.db, os.F_OK):
        db = options.db
    else:
        db = '%s%s%s' % (db_dir,os.path.sep, os.path.basename(options.db) )
    if os.access( options.icon, os.F_OK):
        icon = options.icon
    else:
        icon = ''
    ima=IMApp(db, icon)
    try:
        ima.run()
    except KeyboardInterrupt:
        ima.quit()

if __name__ == "__main__":
    main()

