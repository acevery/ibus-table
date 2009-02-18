#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et ts=4 sts=4
#
# ibus-table - The Tables engine for IBus
#
# filename: ibus-table-speedmeter.py
# 
# display the typing speed
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

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk as gdk
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import threading
import os.path as path
import os 
import sys
import optparse

opt = optparse.OptionParser()

opt.add_option('--daemon','-d',
        action = 'store_true',dest = 'daemon',default=False,
        help = 'Run as daemon, default: %default')

(options, args) = opt.parse_args()

def daemonize(stdout='/dev/null', stderr=None, stdin='/dev/null',
        pidfile=None ):
    '''
    This forks the current process into a daemon.
    The stdin, stdout, and stderr arguments are file names that
    will be opened and be used to replace the standard file descriptors
    in sys.stdin, sys.stdout, and sys.stderr.
    These arguments are optional and default to /dev/null.
    Note that stderr is opened unbuffered, so
    if it shares a file with stdout then interleaved output
    may not appear in the order that you expect.
    '''
    # Do first fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit first parent.
    except OSError, e: 
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/") 
    os.umask(0) 
    os.setsid() 

    # Do second fork.
    try: 
        pid = os.fork()
        if pid > 0: sys.exit(0) # Exit second parent.
    except OSError, e: 
        print 'second fork error'
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'w+')
    se = file(stderr, 'a+', 0)
    pid = str(os.getpid())
    print "Start SpeedMeter with Pid: %s\n"  % pid
    sys.stderr.flush()
    if pidfile: file(pidfile,'w+').write("%s\n" % pid)

    # Redirect standard file descriptors.
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

class Timer(threading.Thread):
    '''add 0 to clist every second, clist must be a list of int'''
    def __init__(self, accumulate):
        super(Timer,self).__init__()
        self.on = True
        self.tlock = threading.RLock()
        self.func = accumulate
        self.sum = 0
    
    def run (self):
        while self.on:
            if self.sum == 0:
                # since we lock in func, so it is safe here
                self.func(0)
            self.sum = (self.sum+1) % 5
            time.sleep(0.2)
    
    def join(self):
        self.on = False
        super(Timer,self).join ()

class Handle(gtk.EventBox):
    def __init__ (self):
        super(Handle, self).__init__()
        self.set_events(
            gdk.BUTTON_PRESS_MASK | \
            gdk.BUTTON_RELEASE_MASK | \
            gdk.BUTTON1_MOTION_MASK)
        self.connect("button_press_event",self.do_button_press_event)
        self.connect("button_release_event",self.do_button_release_event)
        self.connect("motion_notify_event",self.do_motion_notify_event)
        self.__move_begined = False

    def do_button_press_event(self, widget, event, data=None):
        if event.button == 1:
            root = gdk.get_default_root_window()
            try:
                desktop = root.property_get("_NET_CURRENT_DESKTOP")[2][0]
                self.__workarea = root.property_get("_NET_WORKAREA")[2][desktop * 4: (desktop + 1) * 4]
            except:
                self.__workarea = None
            self.__move_begined = True
            toplevel = self.get_toplevel()
            x, y = toplevel.get_position()
            self.__press_pos = event.x_root - x, event.y_root - y
            self.window.set_cursor(gdk.Cursor(gdk.FLEUR))
            return True
        return False

    def do_button_release_event(self, widget, event, data=None):
        if event.button == 1:
            self.__move_begined = False
            del self.__press_pos
            del self.__workarea
            self.window.set_cursor(gdk.Cursor(gdk.HAND1))
            return True

        return False

    def do_motion_notify_event(self, widget, event, data=None):
        if not self.__move_begined:
            return
        toplevel = self.get_toplevel()
        x, y = toplevel.get_position()
        x  = int(event.x_root - self.__press_pos[0])
        y  = int(event.y_root - self.__press_pos[1])

        if self.__workarea == None:
            toplevel.move(x, y)
            return

        if x < self.__workarea[0] and x > self.__workarea[0] - 16:
            x = self.__workarea[0]
        if y < self.__workarea[1] and y > self.__workarea[1] - 16:
            y = self.__workarea[1]

        w, h = toplevel.get_size()
        if x + w > self.__workarea[0] + self.__workarea[2] and \
            x + w < self.__workarea[0] + self.__workarea[2] + 16:
            x = self.__workarea[0] + self.__workarea[2] - w
        if y + h > self.__workarea[1] + self.__workarea[3] and \
            y + h < self.__workarea[1] + self.__workarea[3] + 16:
            y =  self.__workarea[1] + self.__workarea[3] - h

        toplevel.move(x, y)

SPEED_METER_PATH="/org/ibus/table/SpeedMeter"

class SpeedMeter(dbus.service.Object):
    '''Show the typing speed of user'''
    method = lambda **args: \
        dbus.service.method(dbus_interface = "org.ibus.table.SpeedMeter", \
        **args)

    signal = lambda **args: \
        dbus.service.signal(dbus_interface = "org.ibus.table.SpeedMeter", \
        **args)

    def __init__(self, conn):
        self.__conn = conn
        self.__path = SPEED_METER_PATH
        # initiate parent class
        super(SpeedMeter, self).__init__(self.__conn, self.__path)
        # counts for clients
        self.counts = 0
        # list for caculate typing speed
        self.list = [(0, time.time(), 0)]
        # do gui part here
        self.create_ui()
        # timer
        self.full = False
        self.c_time = 0
        self.timer = Timer(self.update_speed)
        gdk.threads_enter()
        self.timer.start()
        gdk.threads_leave()
        # showing
        self.run ()

    # now define the service method
    @method(in_signature='i')
    def Accumulate(self, phrase_len):
        # start typing -> Accumulate(0)
        # commit string -> Accumulate(len(string))
        self.update_speed( phrase_len )

    @method()
    def Reset(self):
        self.reset()
    
    @method()
    def Regist(self):
        self.counts += 1

    @method()
    def Exit(self):
        self.timer.join()
        gtk.main_quit()
        gdk.threads_leave()

    @method()
    def Show(self):
        self.window.move(*self.pos)
        self.window.show()

    @method()
    def Hide(self):
        self.pos = self.window.get_position()
        self.window.hide()

    @method(out_signature='i')
    def report(self):
        return self.counts

    def create_ui(self):
        self.window = gtk.Window(gtk.WINDOW_POPUP)
        #self.window.connect("destroy", lambda w: gtk.main_quit() )
        root = gdk.get_default_root_window()
        try:
            workarea = root.property_get("_NET_WORKAREA")[2]
            right, bottom = workarea[2], workarea[3]
        except:
            right, bottom = root.get_size()
        self.pos = right - 100, bottom -90
        self.window.move(*self.pos)

        #self.window.set_decorated(False)
        # provide grab & moving
        self.event_box = Handle()
        self.event_box.connect("button_press_event",self.do_button_press_event)
        self.event_box.show()
        self.window.add(self.event_box)
        self.event_box.realize()
        self.event_box.window.set_cursor(gdk.Cursor(gdk.HAND1))
        # total frame 
        self.frame = gtk.Frame()
        self.frame.show()
        self.event_box.add(self.frame)
        # for vertical packing
        self.vbox = gtk.VBox()
        self.vbox.show()
        self.frame.add(self.vbox)
        # empty frame for decoration
        self.frame1 = gtk.Frame()
        self.frame1.show()
        self.vbox.pack_start(self.frame1)
        # color of speed label
        self.label_color = gdk.Color(0,0,0xffff)
        # speed label here
        self.speed_label = gtk.Label()
        self.speed_label.set_text('0')
        # make the ratio of whole widget -> G
        self.speed_label.set_size_request(81, 47)
        self.speed_label.set_justify(gtk.JUSTIFY_CENTER)
        self.speed_label.modify_fg(gtk.STATE_NORMAL,
                self.label_color)
        self.speed_label.show()
        self.vbox.pack_start(self.speed_label)
        #self.window.set_resizable(False)
        #self.window.show()
    def run (self):
        gdk.threads_enter()
        gtk.main()

    def update_speed ( self, phrase_len ):
        '''Call this after locking, and then relase lock'''
        now = time.time()
        # only do lock here
        self.timer.tlock.acquire()
        self.list.append( (phrase_len, now) ) 
        self.list = map (lambda x: (x[0], x[1], now - x[1]), self.list )
        self.list = filter (lambda x: x[2] < 61, self.list)
        # unlock here
        self.timer.tlock.release()
        if not self.full:
            self.c_time = self.list[-1][1] - self.list[0][1] 
            self.c_time = (self.c_time > 1 and self.c_time or 1 )
            self.full = (self.c_time >=60)
        speed = ( sum( map( lambda x: x[0], self.list) ) * 60\
                / self.c_time )
        speed = int(speed)
        # now we calculate the color,
        # the color of HSV we want is from (240, 1, 1) -> (360, 1, 1)
        # this is very easy, since S & V are both 1, only H need to take
        # care.
        # we want 10 -> 112 to be marked from blue to red
        if speed > 10:
            # speed > 10
            if speed < 112:
                # 10 < speed < 112
                if speed >= 61:
                    #  61 <= speed < 112
                    # the blue is
                    color = (112-speed) * 5
                    self.label_color.red = 0xffff
                    self.label_color.blue = (color << 8) + color
                else:
                    # 10 < speed < 61
                    # the red is
                    color = (speed-10) * 5
                    self.label_color.red = (color << 8) + color
                    self.label_color.blue = 0xffff
            else:
                # speed >= 112
                    self.label_color.red = 0xffff
                    self.label_color.blue = 0
        else:
            #speed <= 10:
            self.label_color.red=0
            self.label_color.blue = 0xffff
        # update speed label
        self.speed_label.set_text( "%d" % speed )
        self.speed_label.modify_fg(gtk.STATE_NORMAL,
                self.label_color)

    def reset(self):
        self.timer.tlock.acquire()
        self.list = [(0, time.time(), 0)]
        self.full = False
        self.c_time = 0
        self.timer.tlock.release()
        self.update_speed(0)
    
    def do_button_press_event(self, widget, event, data=None):
        if event.button == 3:
            self.reset()
            return True
        return False

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.Bus()
    user = path.basename( path.expanduser('~') )
    name = "org.ibus.table.SpeedMeter.%s" % user
    # check service name first
    request = bus.request_name (name, dbus.bus.NAME_FLAG_DO_NOT_QUEUE)
    if request != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        sys.exit()
    if options.daemon:
        daemonize( '/dev/null', None, '/dev/null' )
    busname = dbus.service.BusName( name, bus )
    gdk.threads_init()
    SpeedMeter(bus)

