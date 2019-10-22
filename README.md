# osu2mc

osu and malody map convert

## usage

select your .osu or .mc files and drag it into convert.py

or

    python convert.py [map1_path] [map2_path]....

## known issues

Only supports green line SV. Malody can't read osu-to-mc red line SV maps correctly.(But time and bpm is correct, playing osu-to-mc-to-osu SV map on osu!mania is OK.)

if you want to convert a red line effect SV map, you can run

    python red_to_green.py [map_path] [bpm]

to translate red line to green line
