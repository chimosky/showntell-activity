import os
import hulahop
from sugar import env
hulahop.startup(os.path.join(env.get_profile_path(), 'gecko'))

from hulahop.webview import WebView

import gtk

win = gtk.Window(gtk.WINDOW_TOPLEVEL)
win.set_size_request(800,600)
win.connect('destroy', gtk.main_quit)
wv = WebView()
#wv.load_uri('file:///home/olpc/Activities/ShowNTell.activity/tw/simple.html')
#wv.load_uri('file:///home/olpc/Activities/ShowNTell.activity/tw/slides.html')
wv.load_uri('file:///home/olpc/isolation/1/uid_to_instance_dir/10001/deck/title.html')
wv.show()

win.add(wv)

win.show()
gtk.main()

