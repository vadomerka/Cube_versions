import vlc
p = vlc.MediaPlayer("static/6612411961515044502_trans_audio.mp3")
import time

p.play()
time.sleep(5)
# print(p)
p.stop()
