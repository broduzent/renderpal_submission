"""Converts any file to any other file (exr to mp4, 25fps) from command line using nuke."""

import nuke
import sys

print(sys.argv[1:])
in_pattern, out_file, in_frame, out_frame, colorspace = sys.argv[1:]

cspace_dict = {
    "default": 0,
    "linear": 1,
    "srgb": 2,
    "rec709": 3,
    "cineon": 4,
    "gamma1.8": 5,
    "gamma2.2": 6,
    "gamma2.4": 7,
    "gamma2.6": 8,
    "panalog": 9,
    "redlog": 10,
    "viperlog": 11,
    "alexav3logc": 12,
    "plogin": 13,
    "slog": 14,
    "slog1": 15,
    "slog2": 16,
    "slog3": 17,
    "clog": 18,
    "log3g10": 19,
    "log3g12": 20,
    "hybridloggamma": 21,
    "protune": 22,
    "bt1886": 23,
    "st2084": 24,
    "blackmagicfilmgeneration5": 25,
    "arrilogc4": 26,
}

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
w.setInput(0, r)
w.knob("file_type").setValue("mov")
print("Node setup done")
r.knob("file").setValue(in_pattern)
r.knob("first").setValue(in_frame)
r.knob("last").setValue(out_frame)
w.knob("file").setValue(out_file)
w.knob("colorspace").setValue(cspace_dict[colorspace.lower()])
try:
    w.knob("mov64_fps").setValue(25)
    w.knob("mov64_codec").setValue(14)  # H.264
except:
    print("Not setting mov fps")
print("Path setup done")
nuke.execute("Write1", in_frame, out_frame)
print("All done!")
