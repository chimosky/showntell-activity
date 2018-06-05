#!/usr/bin/python

# ZetCode PyGtk tutorial
#
# This example shows a TreeView widget
# in a list view mode
#
# author: jan bodnar
# website: zetcode.com
# last edited: February 2009

from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.datastore import datastore

from path import path
from datetime import datetime


class Cpxoview(Gtk.VBox):
    def __init__(self, activity, deck):
        print 'cpxoview init'
        self.activity = activity
        Gtk.VBox.__init__(self)

        vbox = Gtk.VBox(False, 8)
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(sw, True, True, 0)
        treeView = Gtk.TreeView()
        treeView.connect("row-activated", self.on_activated)
        treeView.set_rules_hint(True)
        sw.add(treeView)
        self.create_columns(treeView)
        self.treeView = treeView
        self.deck = deck
        self.add(vbox)
        self.show_all()

    def create_columns(self, treeView):
        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", rendererText, text=1)
        column.set_sort_column_id(1)
        treeView.append_column(column)
        rendererText = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Date", rendererText, text=2)
        column.set_sort_order(Gtk.SortType.ASCENDING)
        column.set_sort_column_id(2)
        treeView.append_column(column)

    def get_treeView(self):
        return self.treeView

    def set_store(self, src):
        print 'set_store', src
        store = Gtk.ListStore(str, str, str)
        # get objects from the local datastore
        if src == "datastore":
            self.ds_objects, num_objects = datastore.find(
                {'mime_type': ['application/x-classroompresenter']})
            for f in self.ds_objects:
                try:
                    object = f.object_id
                except BaseException:
                    print 'find object_id failed'
                try:
                    title = f.metadata['title']
                except BaseException:
                    title = ""
                try:
                    t = f.metadata['timestamp']
                    timestamp = datetime.fromtimestamp(t)
                except BaseException:
                    timestamp = ""
                store.append([object, title, timestamp])
                f.destroy()
        elif src == "activity":
            # source is activity bundle
            srcdir = path(activity.get_bundle_path()) / \
                'resources' / 'Presentations'
            for f in srcdir.files('*.cpxo'):
                store.append([f.name, "", f.getctime()])
        else:
            print 'error in src', src
        print 'return cpxo store'
        return store

    def on_activated(self, widget, row, col):

        print 'cpxo on_activated'
        model = widget.get_model()
        print 'row', model[row][0], model[row][1], model[row][2]
        object = datastore.get(model[row][0])
        fn = object.file_path
        print 'object filename', path(fn).exists(), fn
        # open slideshow, set Navigation toolbar current
        self.activity.read_file(fn)
        for object in self.ds_objects:
            object.destroy()
        self.activity.set_screen(0)
