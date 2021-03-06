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

import gi
gi.require_version('Gst', '1.0')
import os
import time
from path import path
import logging
import subprocess
from sugar3.activity import activity

from gi.repository import Gtk
from gi.repository import Gst

AUDIOPATH = path(activity.get_activity_root()) / 'data' / 'temp.wav'


class TextArea(Gtk.HBox):

    # Constructor
    def __init__(self, deck, work_path):
        Gtk.HBox.__init__(self)

        self.__logger = logging.getLogger('TextArea')
        self.__deck = deck
        self.__work_path = work_path
        self.__text_area = Gtk.Entry()
        self.render_text_area()
        self.__deck.connect('slide-redraw', self.update_text)
        self.__text_area.connect('changed', self.text_changed)
        self.__logger.debug("Constructed")

        """
            #initialize audio record pipeline
            player = Gst.Pipeline.new("player")
            #source = Gst.ElementFactory.make("alsasrc", "alsa-source")
            source = Gst.ElementFactory.make("filesrc", "file-source")
            player.add(source)
            parse = Gst.ElementFactory.make("wavparse", "parser")
            player.add(parse)
            convert = Gst.ElementFactory.make("audioconvert", "converter")
            player.add(convert)
            enc = Gst.ElementFactory.make("vorbisenc", "vorbis-encoder")
            player.add(enc)
            create = Gst.ElementFactory.make("oggmux", "ogg-create")
            player.add(create)
            fileout = Gst.ElementFactory.make("filesink", "sink")
            player.add(fileout)
            source.link(parse) 
            parse.link(convert)
            convert.link(enc) 
            enc.link(create) 
            create.link(fileout)
            self.__player = player
            self.__source = source
            self.__fileout = fileout
            """

        # initialize convert pipeline
        p = "filesrc location=" + AUDIOPATH + " ! wavparse "
        p = p + "! audioconvert ! vorbisenc ! oggmux "
        p = p + "! filesink location="
        self.__pipeline = p

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
        self.pack_start(
            self.create_bbox(
                title="Audio Controls"),
            False,
            False,
            0)
        self.pack_start(self.__text_area, True, True, 0)

        # show widgets
        self.__text_area.show()
        self.show()

    # Clear text in entry box
    def clear_text(self, widget, event):
        self.__text_area.set_text("")

    # Start Recording
    def record(self, button):
        if not button.get_active():
            # we are recording, stop and save clip
            subprocess.call("killall -q arecord", shell=True)
            n = self.__deck.getIndex()
            self.__audiofile = self.__deck.getSlideClip(n)
            if not self.__audiofile:
                self.__audiofile = self.__deck.get_SlideTitle() + '.ogg'
            audiofile = self.__work_path / 'deck' / self.__audiofile
            print 'audiofile', n, audiofile
            if audiofile.exists():
                subprocess.call("rm -rf " + str(audiofile), shell=True)
            self.__deck.setSlideClip(audiofile.name, n)
            # convert to ogg file
            pipeline = self.__pipeline + audiofile
            subprocess.call("gst-launch-1.0 " + pipeline, shell=True)
            subprocess.call("amixer cset numid=11 off", shell=True)
            # reset mic boost
            print 'mic boost off', n, self.__audiofile, path(self.__audiofile).exists()
        else:
            # turn on mic boost (xo)
            print 'turn on mic boost'
            subprocess.call("amixer cset numid=11 on", shell=True)
            #self.__fileout.set_property("location", self.__audiofile)
            #self.__source.set_property("location", AUDIOPATH)
            # self.__player.set_state(Gst.State.PLAYING)
            print 'recording started'
            self.__pid = subprocess.Popen(
                "arecord -f cd " + AUDIOPATH, shell=True)

    # Play Audio Clip
    def play(self, button):
        if button.get_active():
            # play clip
            clip = self.__deck.getSlideClip()
            print 'play clip:', clip
            if clip:
                cmd = "gst-launch-1.0 filesrc location=" + clip
                cmd = cmd + " ! decodebin ! audioconvert ! alsasink"
                self.__pid = subprocess.Popen(cmd, shell=True)
        else:
            # we are playing and need to stop
            subprocess.call("killall -q gst-launch-1.0", shell=True)

    # Create buttons for audio controls
    def create_bbox(
            self,
            title=None,
            spacing=0,
            layout=Gtk.ButtonBoxStyle.SPREAD):
        frame = Gtk.Frame()
        frame.set_label(title)

        bbox = Gtk.HButtonBox()
        bbox.set_border_width(5)
        bbox.set_layout(layout)
        bbox.set_spacing(spacing)

        button = Gtk.ToggleButton('gtk-media-record')
        button.set_use_stock(True)
        button.connect("clicked", self.record)
        bbox.pack_start(button, False, False, 0)

        button = Gtk.ToggleButton('gtk-media-play')
        button.set_use_stock(True)
        button.connect("clicked", self.play)
        bbox.pack_start(button, False, False, 0)

        frame.add(bbox)
        return frame
