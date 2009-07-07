gst-launch-0.10 filesrc location=/tmp/temp.wav ! wavparse ! vorbisenc ! filesink location = /tmp/temp.ogg
