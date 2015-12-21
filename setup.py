#!/usr/bin/env python
try:
	from sugar3.activity import bundlebuilder
	bundlebuilder.start()
except ImportError:
	import os
	#os.system("find ./ | sed 's,^./,ClassroomPresenter.activity/,g' > MANIFEST")
	os.system('rm ClassroomPresenter.xo')
	os.chdir('..')
	os.system('zip -r ClassroomPresenter.xo ClassroomPresenter.activity')
	os.system('mv ClassroomPresenter.xo ./ClassroomPresenter.activity')
	os.chdir('ClassroomPresenter.activity')
