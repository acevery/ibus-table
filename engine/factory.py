# -*- coding: utf-8 -*-
# vim: set noet ts=4:
#
# scim-python
#
# Copyright (c) 2008-2008 Yu Yuwei <acevery@gmail.com>
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

import ibus
import table
import tabsqlitedb
import os
import dbus

from gettext import dgettext
_  = lambda a : dgettext ("ibus-table", a)
N_ = lambda a : a

fatory_base_path = "/com/redhat/IBus/engines/table/%s/factory"
engine_base_path = "/com/redhat/IBus/engines/table/%s/engine/"

class EngineFactory (ibus.EngineFactoryBase):
    """Table IM Engine Factory"""
    def __init__ (self, bus, db, icon):
        import locale
        # here the db should be the abs path to sql db
        # this is the backend sql db we need for our IME
        # we need get lots of IME property from this db :)
        #self.db = tabsqlitedb.tabsqlitedb( name = database )
        
        # the name for dbus
        self.dbusname = os.path.basename(db).replace('.db','')
        self.factory_path = fatory_base_path % self.dbusname
        self.engine_path = engine_base_path % self.dbusname
        udb = os.path.basename(db).replace('.db','-user.db') 
        self.db = tabsqlitedb.tabsqlitedb( name = db,user_db = udb )
        ulocale = locale.getdefaultlocale ()[0].lower()
        self.name     =  self.db.get_ime_property ('name.%s' % ulocale) 
        if not self.name:
            self.name         = _( self.db.get_ime_property ('name') )
        self.uuid        = self.db.get_ime_property ('uuid')
        self.authors    = self.db.get_ime_property ('author')
        if icon:
            self.icon = icon
        else:
            self.icon = '%s%s%s%s%s' % ( os.getenv("IBUS_TABLE_LOCATION") ,
                os.path.sep,'icons',os.path.sep, self.db.get_ime_property ('icon') )
        self.credits    = self.db.get_ime_property ('credit')
        self.lang        = self.db.get_ime_property ('languages') 
        # now we construct the info for ibus
        self.info = [
            self.name,
            self.lang,
            self.icon,
            self.authors,
            self.credits
            ]
        
        # init factory
        self.bus = bus
        super(EngineFactory,self).__init__(self.info, table.tabengine, self.engine_path, bus, self.factory_path)
        self.engine_id=1
        self.db.db.commit()
        try:
            bus = dbus.Bus()
            user = os.path.basename( os.path.expanduser('~') )
            self._sm_bus = bus.get_object ("org.ibus.table.SpeedMeter.%s"\
                    % user, "/org/ibus/table/SpeedMeter")
            self._sm =  dbus.Interface(self._sm_bus,\
                    "org.ibus.table.SpeedMeter") 
            self._sm.Regist()
        except:
            self._sm = None
    
    def create_engine(self):
        # because we need db to be past to Engine
        engine = table.tabengine(self.bus, self.engine_path + str(self.engine_id), self.db)
        self.engine_id += 1
        return engine.get_dbus_object()

    def do_destroy (self):
        '''Destructor, which finish some task for IME'''
        # we need to sync the temp userdb in memory to the user_db on disk
        self.db.sync_usrdb ()
        print "Have synced user db"
        try:
            self._sm.Exit()
        except:
            pass
        super(EngineFactory,self).do_destroy()


