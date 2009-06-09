# -*- mode:python; tab-width:4; indent-tabs-mode:t;  -*-

# textarea.py
#
# Class to show, save, submit text entries
# 
# W.Burnside <wburnsid@u.washington.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import os, time
from path import path
import pygtk
import gtk
import logging
import subprocess
from sugar.activity import activity

import pygst
pygst.require("0.10")
import gst

class TextArea(gtk.HBox):


        # Constructor
        def __init__(self, deck):
            gtk.HBox.__init__(self)
            
            self.__logger = logging.getLogger('TextArea')
            self.__deck = deck
            self.__text_area = gtk.Entry()
            self.render_text_area()
            self.__record=False
            self.__play=False
            self.__deck.connect('slide-redraw', self.update_text)
            self.__text_area.connect('changed', self.text_changed)
            self.__logger.debug("Constructed")

            """            
            #initialize audio record pipeline
            player = gst.Pipeline("player")
            #source = gst.element_factory_make("alsasrc", "alsa-source")
            source = gst.element_factory_make("filesrc", "file-source")
            player.add(source)
            parse = gst.element_factory_make("wavparse", "parser")
            player.add(parse)
            convert = gst.element_factory_make("audioconvert", "converter")
            player.add(convert)
            enc = gst.element_factory_make("vorbisenc", "vorbis-encoder")
            player.add(enc)
            create = gst.element_factory_make("oggmux", "ogg-create")
            player.add(create)
            fileout = gst.element_factory_make("filesink", "sink")
            player.add(fileout)
            gst.element_link_many(source, parse, convert, enc, create, fileout)
            self.__player = player
            self.__source = source
            self.__fileout = fileout
            """        

        def update_text(self, widget):
            selfink, text = self.__deck.getSelfInkOrSubmission()
            self.__text_area.set_text(text)
            if self.__deck.getActiveSubmission() == -1 and not self.__deck.getIsInitiating():
                self.__text_area.set_sensitive(True)
            else:
                self.__text_area.set_sensitive(False)
        
        def text_changed(self, entry):
            if self.__deck.getActiveSubmission() == -1:
                self.__deck.setSlideText(self.__text_area.get_text())
            
        def render_text_area(self, widget=None):
            
            # pack widgets
            self.pack_start(self.create_bbox(title="Audio Controls"), False, False, 0)
            self.pack_start(self.__text_area, True, True, 0)
            
            # show widgets
            self.__text_area.show()
            self.show()
        
        # Clear text in entry box
        def clear_text(self, widget, event):
            self.__text_area.set_text("")
                
        # Start Recording
        def record(self, params):
            if self.__record:
                #we are recording, stop and save clip
                subprocess.call("killall -q arecord", shell=True)
                #convert to ogg file
                pipeline = "filesrc location=/tmp/temp.wav ! wavparse ! audioconvert ! vorbisenc ! oggmux ! filesink location=" + self.__audiofile
                print 'pipeline', pipeline
                subprocess.call("gst-launch-0.10 " + pipeline, shell=True)
                #self.__player.set_state(gst.STATE_PLAYING)
                #time.sleep(10)
                #self.__player.set_state(gst.STATE_NULL)
                self.__record = False
                self.__deck.setSlideClip(self.__audiofile, n = self.__deck.getIndex())
                self.__deck.save()
                self.__deck.reload()
                #reset mic boost (xo)
                subprocess.call("amixer cset numid=11 off", shell = True)
                print 'recording stopped'
            else:
                self.__record = True
                #what is name of clip? If it exists, rm it
                self.__audiofile = self.__deck.getSlideClip()
                if path(self.__audiofile).exists():
                    subprocess.call("rm -rf " + str(self.__audiofile), shell=True)
                else:
                    self.__audiofile = path(self.__deck.getDeckPath()) / 'slide' +  str(self.__deck.getIndex()) + '.ogg'
                #turn on mic boost (xo)
                print 'turn on mic boost'
                subprocess.call("amixer cset numid=11 on", shell=True)
                print 'record clip:', self.__audiofile
                #self.__fileout.set_property("location", self.__audiofile)
                #self.__source.set_property("location", "/tmp/temp.wav")
                #self.__player.set_state(gst.STATE_PLAYING)
                print 'recording started'
                subprocess.call("arecord -f cd -d 10 /tmp/temp.wav", shell=True)

        # Play Audio Clip
        def play(self, params):
            if self.__play:
                #we are playing and need to stop
                subprocess.call("killall -q gst-launch-0.10", shell=True)
                self.__play = False
            else:
                #play clip
                self.__deck.save()
                clip = self.__deck.getSlideClip()
                #clip = "/home/olpc/Activities/ShowNTell.activity/resources/test.ogg"
                print 'play clip:', clip
                if clip:
                    self.__play = True
                    subprocess.call("gst-launch-0.10 filesrc location=" + clip + " ! decodebin ! audioconvert ! alsasink", shell = True)
                    self.__play = False

        # Create buttons for audio controls
        def create_bbox(self, title=None, spacing=0, layout=gtk.BUTTONBOX_SPREAD):
            frame = gtk.Frame(title)
            bbox = gtk.HButtonBox()
            bbox.set_border_width(5)
            bbox.set_layout(layout)
            bbox.set_spacing(spacing)

            button = gtk.Button(stock='gtk-media-record')
            button.connect("clicked", self.record)
            bbox.pack_start(button, False, False, 0)

            button = gtk.Button(stock='gtk-media-play')
            button.connect("clicked", self.play)
            bbox.pack_start(button, False, False, 0)

            frame.add(bbox)
            return frame
