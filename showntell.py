# -*- mode:python; tab-width:4; indent-tabs-mode:t;  -*-

# showntell.py
#
# Derived from:
#
# Classroom Presenter for the XO Laptop
# Main class
# B. Mayton <bmayton@cs.washington.edu>
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

from sugar.activity import activity
from sugar.datastore import datastore
import logging

import sys, os
import subprocess
import atexit, signal
import gtk
import zipfile

import slideviewer
import sidebar
import sliderenderer
import slideshow
import textarea
import toolbars
import utils
import shared
import time
import pdb

import listview
import cpxoview

import hulahop
from sugar import env
hulahop.startup(os.path.join(env.get_profile_path(), 'gecko'))
from hulahop.webview import WebView

SLIDESHOW_TOOLBAR = 1
NAVIGATION_TOOLBAR = 2
TITLE_SLIDE = "title.html"

class ShowNTell(activity.Activity):
        
    def __init__(self, handle):
        #pdb.set_trace()
        atexit.register(self.report_exit, 'message')
        signal.signal(signal.SIGINT, self.signal_exit)
        signal.signal(signal.SIGABRT, self.signal_exit)
        signal.signal(signal.SIGTERM, self.signal_exit)
        signal.signal(signal.SIGSEGV, self.signal_exit)
        signal.signal(signal.SIGQUIT, self.signal_exit)
        activity.Activity.__init__(self, handle)

        self.__logger = logging.getLogger('ClassroomPresenter')
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

        # Find our instance path
        self.__work_path = os.path.join(self.get_activity_root(), 'instance')
        self.__deck_dir = os.path.join(self.__work_path, 'deck')
        if '-o' not in sys.argv:
            try:
                os.mkdir(self.__deck_dir)
            except Exception, e:
                self.__logger.debug("Caught exception and continuing: %s", e)
                print 'deck_dir exists'
                subprocess.call("rm -rf " + self.__deck_dir + "/*", shell=True)

        self.__rsrc_dir = os.path.join(activity.get_bundle_path(), 'resources')
        self.__logger.debug("Found deck directory: %s", self.__deck_dir)    
    
        # Copy the splash screen to the working directory
        self.__title_slide_name = TITLE_SLIDE
        utils.copy_file(os.path.join(self.__rsrc_dir, self.__title_slide_name),
                os.path.join(self.__deck_dir, self.__title_slide_name))
        
        # Create a slide deck object
        self.__deck = slideshow.Deck(self.__title_slide_name, self.__deck_dir)

        # Set up activity sharing
        self.__shared = shared.Shared(self, self.__deck, self.__work_path)
        
        # Create a renderer for slides
        self.__renderer = sliderenderer.Renderer(self, self.__deck)
        
        # Set up the main canvas
        self.__slide_view = gtk.HBox()
        self.set_canvas(self.__slide_view)
        
        # Set up Main Viewer box
        self.__main_view_box = gtk.VBox()
        #here enter a gtk widget in place of self.__slide
        #pack this common widget to self.__main_view_box
        #then render each 'screen' to this common widget as needed
        self.__slide = slideviewer.SlideViewer(self.__deck, self.__renderer)
        self.__text_area = textarea.TextArea(self.__deck)
        self.__image_chooser = listview.Listview(self, self.__deck)
        self.__slideshow_chooser = cpxoview.Cpxoview(self, self.__deck)
        self.__html_slide = gtk.EventBox()
        self.__screens = []
        self.__main_view_box.pack_start(self.__slide, True, True, 5)
        self.__screens.append(self.__slide)
        self.__main_view_box.pack_start(self.__image_chooser, True, True, 5)
        self.__screens.append(self.__image_chooser)
        self.__main_view_box.pack_start(self.__slideshow_chooser, True, True, 5)
        self.__screens.append(self.__slideshow_chooser)
        self.__main_view_box.pack_start(self.__html_slide, True, True, 5)
        self.__screens.append(self.__html_slide)
        self.__main_view_box.pack_start(self.__text_area, False, False, 0)
        
        # Create our toolbars
        makeTB = toolbars.MakeToolBar(self, self.__deck)
        navTB = toolbars.NavToolBar(self, self.__shared, self.__deck)
        inkTB = toolbars.InkToolBar(self.__slide, self.__deck)
        
        # Create the standard activity toolbox; add our toolbars
        toolbox = activity.ActivityToolbox(self)
        toolbox.add_toolbar("Slideshow", makeTB)
        toolbox.add_toolbar("Navigation",navTB)
        toolbox.add_toolbar("Ink", inkTB)
        self.set_toolbox(toolbox)
        toolbox.show()
        self.__toolbox = toolbox

        # Open with slideshow toolbar
        toolbox.set_current_toolbar(SLIDESHOW_TOOLBAR)
        
        # Set up the side scrollbar widget
        self.__side_bar = sidebar.SideBar(self.__deck, self.__renderer)
        self.__side_bar.set_size_request(225, 100)
        
        # Set up a separator for the two widgets
        separator = gtk.VSeparator()
        
        # Pack widgets into main window
        self.__slide_view.pack_start(self.__main_view_box, True, True, 0)
        self.__slide_view.pack_start(separator, False, False, 5)
        self.__slide_view.pack_start(self.__side_bar, False, False, 0)
        
        # Show all widgets
        self.__slide_view.show_all()
        self.__main_view_box.show()
        self.__slide.show()
        self.__text_area.show()
        self.__image_chooser.hide()
        self.__slideshow_chooser.hide()
        #self.__html_viewer.hide()
        separator.show()
        self.__side_bar.show_all()
        
        # Set up the progress view
        self.__progress_max = 1.0
        self.__progress_cur = 0.01
        self.__progress_view = gtk.VBox()
        self.__progress_lbl = gtk.Label("Loading slide deck...")
        self.__progress_bar = gtk.ProgressBar()
        self.__progress_view.pack_start(self.__progress_lbl, True, False, 5)
        #self.__progress_view.pack_start(self.__progress_bar, False, False, 5)
        self.__progress_bar.set_fraction(self.__progress_cur / self.__progress_max)
        
        self.__shared.connect('deck-download-complete', self.dl_complete_cb)

    def report_exit(self, message):
        print 'activity exited', message

    def signal_exit(signal, frame):
        print 'activity exited', signal

    def dl_complete_cb(self, widget):
        self.do_slideview_mode()
    
    def do_slideview_mode(self):
        self.set_canvas(self.__slide_view)
        self.__slide_view.show_all()
    
    def set_progress_max(self, maxval):
        self.__progress_max = maxval
        self.__progress_bar.set_fraction(float(self.__progress_cur) / float(self.__progress_max))
    
    def do_progress_view(self):
        self.set_canvas(self.__progress_view)
        self.__progress_view.show_all()
        
    def set_progress(self, val):
        self.__progress_cur = val
        self.__progress_bar.set_fraction(float(self.__progress_cur) / float(self.__progress_max))
        
    #resume from journal    
    def read_file(self, file_path):
        self.__logger.debug("read_file " + str(file_path))
        ftype = utils.getFileType(file_path)
        z = zipfile.ZipFile(file_path, "r")
        for i in z.infolist():
            f = open(os.path.join(self.__deck_dir, i.filename), "wb")
            f.write(z.read(i.filename))
            f.close()
        z.close()
        self.__deck.set_title(self.metadata['title'])
        self.__deck.reload()
        self.__toolbox.set_current_toolbar(NAVIGATION_TOOLBAR)
        newindex = 0
        if 'current_index' in self.metadata:
            newindex = int(self.metadata.get('current_index', '0'))
        self.__deck.goToIndex(newindex, is_local=False)
    
    #save state in journal for resume
    def write_file(self, file_path):
        print 'write_file', self.__toolbox.get_current_toolbar(), str(file_path)
        if self.__toolbox.get_current_toolbar() > 0:
            return
        self.__logger.debug("write_file " + str(file_path))
        self.metadata['title'] = self.__deck.get_title(2)
        self.metadata['mime_type'] = "application/x-classroompresenter"
        self.metadata['current_index'] = str(self.__deck.getIndex())
        self.__deck.save()
        z = zipfile.ZipFile(file_path, "w")
        root, dirs, files = os.walk(self.__deck_dir).next()
        for f in files:
            z.write(os.path.join(root, f), f)
        z.close()
        
    def get_shared_activity(self):
        return self._shared_activity     
        
    def set_screen(self,scrn):
        print 'set_screen', scrn
        self.__screens[0].hide()
        print 'screen 0 hidden'
        self.__screens[1].hide()
        print 'screen 1 hidden'
        self.__screens[2].hide()
        print 'screen 2 hidden'
        self.__screens[3].hide()
        print 'screen 3 hidden'
        self.__screens[scrn].show()
        print 'screen', scrn, 'shown'
        return self.__screens[scrn]

