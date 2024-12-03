"""Converts any file to any other file (exr to mp4, 25fps) from command line using nuke."""

import nuke
import sys

print(sys.argv[1:])
in_pattern, out_file, in_frame, out_frame = sys.argv[1:]

in_frame = int(in_frame[-4:])
out_frame = int(out_frame[-4:])
in_pattern = in_pattern.replace("\\", "/")
out_file = out_file.replace("\\", "/")

print(f"Reading frames from {in_pattern}")
print(f"Using frames {in_frame} to {out_frame}")
print(f"Writing frames to {out_file}")

nuke.root()['fps'].setValue(25)
r = nuke.nodes.Read()
w = nuke.nodes.Write()
w.setInput( 0, r )
print("Node setup done")
r.knob("file").setValue(in_pattern)
r.knob("first").setValue(in_frame)
r.knob("last").setValue(out_frame)
w.knob("file").setValue(out_file)
print("Path setup done")
nuke.execute("Write1", in_frame, out_frame)
print("All done!")