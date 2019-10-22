import sys
import os
import osu_mania
import mc
import re


match_filename = r"(.+)\.(.+)"


def convert(filename):
    matched = re.match(match_filename, filename)
    if not matched:
        return
    name = matched.group(1)
    filetype = matched.group(2).lower()
    if filetype == "osu":
        mc.write(osu_mania.parse(filename), name + ".mc")
    elif filetype == "mc":
        osu_mania.write(mc.parse(filename), name + ".osu")


for index, arg in enumerate(sys.argv[1:]):
    print(f'({str(index+1)}/{str(len(sys.argv)-1)}) Converting "{arg}"')
    convert(arg)
    print("Complete~")

os.system("pause")

