# -*- mode:python; tab-width:4; indent-tabs-mode:t;  -*-

import os
from gi.repository import Gtk


def getFileType(filename):
    return os.path.basename(filename).split('.').pop()


def copy_file(src, dest):
    f1 = open(src, "rb")
    data = f1.read()
    f1.close()
    f2 = open(dest, "wb")
    f2.write(data)
    f2.close()


def run_dialog(header, msg):
    """Pops up a blocking dialog box with 'msg'"""
    dialog = Gtk.Dialog(
        "Hola",
        None,
        Gtk.DialogFlags.MODAL,
        (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))

    hbox = Gtk.HBox(False, 12)
    hbox.set_border_width(12)
    dialog.vbox.pack_start(hbox, True, True, 0)
    hbox.show()

    label = Gtk.Label(str(msg))
    hbox.pack_start(label, False, False, 0)
    label.show()

    dialog.run()
    dialog.destroy()
