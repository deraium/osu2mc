import sys
import json
import re
import time
import os
import fractions


class Beat(object):
    def __init__(self, a: int = 0, b: int = 0, c: int = 1):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return f"[{str(self.a)}, {str(self.b)}, {str(self.c)}]"

    def reduction(self):
        while self.b >= self.c:
            self.a += 1
            self.b -= self.c
        while self.b < 0:
            self.a -= 1
            self.b += self.c
        if self.b == 0:
            self.c = 1
        fraction = fractions.Fraction(self.b, self.c)
        self.b = fraction.numerator
        self.c = fraction.denominator
        return self

    def __iadd__(self, beat_2):
        self.a += beat_2.a
        self.b = self.b * beat_2.c + self.c * beat_2.b
        self.c *= beat_2.c
        self.reduction()
        return self

    def __sub__(self, beat_2):
        beat = Beat()
        beat.a = self.a - beat_2.a
        beat.b = self.b * beat_2.c - self.c * beat_2.b
        beat.c = self.c * beat_2.c
        beat.reduction()
        return beat

    def __gt__(self, beat_2):
        if self.a < beat_2.a:
            return False
        elif self.a > beat_2.a:
            return True
        elif (self.b / self.c) > (beat_2.b / beat_2.c):
            return True
        return False

    def __ge__(self, beat_2):
        if self.a < beat_2.a:
            return False
        elif self.a > beat_2.a:
            return True
        elif (self.b / self.c) < (beat_2.b / beat_2.c):
            return False
        return True

    def __eq__(self, beat_2):
        return self.a == beat_2.a and (self.b / self.c) == (beat_2.b / beat_2.c)


class Note(object):
    def __init__(self):
        self.start = 0.0
        self.end = 0.0
        self.column = 0
        self.hitsound = ""
        self.volumn = 0


class BPM(object):
    def __init__(self):
        self.time = 0
        self.bpm = 0


class ManiaMap(object):
    def __init__(self):
        self.audio = None
        self.leadin = 0
        self.preview = 0
        self.title = None
        self.title_unicode = None
        self.artist = None
        self.artist_unicode = None
        self.creator = None
        self.version = None
        self.background = None
        self.key_amount = 0
        self.notes = []
        self.bpms = []


match_item = r"(.+?): *(.+)"
match_section = r"[\t ]*\[(.+)\][\t ]*"
match_bpm = r"[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*"
match_note = r"[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*:[\t ]*(.+)[\t ]*"
match_hitsound = r"(?:.+:)*(.+):(.*)"


def accu_bpm(bpm: float, precision: float = 0.001, limit: int = 8):
    origin_bpm = bpm
    for i in range(0, limit):
        if abs(bpm - int(bpm + 0.5)) < precision:
            return int(bpm) / (10 ** i)
        bpm *= 10.0
    return origin_bpm


def time2beat(time: float, millseconds_per_beat: float, max_error: float = 1.0):
    a = 0
    t = time
    while t > millseconds_per_beat:
        t -= millseconds_per_beat
        a += 1
    if abs(t) <= max_error:
        return Beat(a, 0, 1)
    if abs(t - millseconds_per_beat) <= max_error:
        return Beat(a + 1, 0, 1)
    b = 1
    c = 2
    r = b / c * millseconds_per_beat
    while abs(t - r) >= max_error:
        b += 1
        if b == c:
            b = 1
            c += 1
        r = b / c * millseconds_per_beat
    return Beat(a, b, c).reduction()


def beat2time(beat: Beat, millseconds_per_beat: float):
    return (beat.a + (beat.b / beat.c)) * millseconds_per_beat


def parse_osu(filename):
    file = open(filename, "r", encoding="utf-8")
    map = ManiaMap()
    section = None
    previous_bpm = 0.0
    for line in file.readlines():
        line = line[0:-1]
        matched = re.match(match_section, line)
        if matched:
            section = matched.group(1)
        if section == None:
            continue
        if section == "General" or section == "Metadata" or section == "Difficulty":
            matched = re.match(match_item, line)
            if matched:
                attribute = matched.group(1)
                value = matched.group(2)
                if attribute == "AudioFilename":
                    map.audio = value
                elif attribute == "AudioLeadIn":
                    map.leadin = value
                elif attribute == "PreviewTime":
                    map.preview = value
                elif attribute == "Title":
                    map.title = value
                elif attribute == "TitleUnicode":
                    map.title_unicode = value
                elif attribute == "Artist":
                    map.artist = value
                elif attribute == "ArtistUnicode":
                    map.artist_unicode = value
                elif attribute == "Creator":
                    map.creator = value
                elif attribute == "Version":
                    map.version = value
                elif attribute == "CircleSize":
                    map.key_amount = int(value)
            continue
        if section == "TimingPoints":
            matched = re.match(match_bpm, line)
            if matched:
                bpm = BPM()
                bpm.time = float(matched.group(1))
                bpm.bpm = float(matched.group(2))
                if bpm.bpm > 0:
                    bpm.bpm = 60000.0 / bpm.bpm
                    bpm.bpm = accu_bpm(bpm.bpm)
                    previous_bpm = bpm.bpm
                else:
                    bpm.bpm = -previous_bpm * 100.0 / bpm.bpm
                    bpm.bpm = accu_bpm(bpm.bpm)
                map.bpms.append(bpm)
            continue
        if section == "HitObjects":
            matched = re.match(match_note, line)
            if matched:
                note = Note()
                note.column = int(int(matched.group(1)) / 512 * map.key_amount)
                note.start = float(matched.group(3))
                note.end = float(matched.group(6))
                extras = matched.group(7)
                extra_matched = re.match(match_hitsound, extras)
                if extra_matched:
                    hitsound_file = extra_matched.group(2)
                    if len(hitsound_file) > 0:
                        note.hitsound = hitsound_file
                        note.volumn = float(extra_matched.group(1))
                map.notes.append(note)
    file.close()
    return map


def parse_mc(filename):
    file = open(filename, "r", encoding="utf-8")
    map = ManiaMap()
    json_datas = file.read()
    mc_map = json.loads(json_datas)
    map.artist = mc_map["meta"]["song"]["artist"]
    map.artist_unicode = mc_map["meta"]["song"]["artist"]
    map.creator = mc_map["meta"]["creator"]
    map.key_amount = mc_map["meta"]["mode_ext"]["column"]
    map.leadin = 0
    map.preview = mc_map["meta"]["preview"]
    map.title = mc_map["meta"]["song"]["title"]
    map.title_unicode = mc_map["meta"]["song"]["title"]
    map.version = mc_map["meta"]["version"]
    time_start = 0.0
    audio = ""
    note_special = mc_map["note"][0]
    if note_special.get("type", 0) == 1:
        time_start = note_special["offset"]
        audio = note_special["sound"]
    else:
        note_special = mc_map["note"][-1]
        if note_special.get("type", 0) == 1:
            time_start = note_special["offset"]
            audio = note_special["sound"]
        else:
            for mc_note in mc_map["note"][1:-1]:
                if mc_note.get("type", 0) == 1:
                    time_start = mc_note["offset"]
                    audio = mc_note["sound"]
                    break
    bpms = []
    previous_time = time_start
    previous_bpm = 200.0
    previous_beat = Beat()
    for mc_bpm in mc_map["time"]:
        bpm = BPM()
        beat = Beat(*mc_bpm["beat"])
        bpm.time = previous_time + beat2time(
            beat - previous_beat, 60000.0 / previous_bpm
        )
        bpm.bpm = mc_bpm["bpm"]
        bpms.append(bpm)
        previous_time = bpm.time
        previous_bpm = bpm.bpm
        previous_beat = beat
    map.bpms = bpms
    notes = []
    previous_bpm_index = 0
    next_bpm_index = 1
    previous_time = time_start
    for mc_note in mc_map["note"]:
        column = mc_note.get("column", None)
        if column == None:
            continue
        note_beat = Beat(*mc_note["beat"])
        while next_bpm_index < len(bpms):
            next_bpm_beat = Beat(*mc_map["time"][next_bpm_index]["beat"])
            if note_beat >= next_bpm_beat:
                previous_bpm_beat = Beat(*mc_map["time"][previous_bpm_index]["beat"])
                previous_time += beat2time(
                    next_bpm_beat - previous_bpm_beat,
                    60000.0 / bpms[previous_bpm_index].bpm,
                )
                previous_bpm_index += 1
                next_bpm_index += 1
            else:
                break
        previous_bpm_beat = Beat(*mc_map["time"][previous_bpm_index]["beat"])
        note = Note()
        note.column = column
        note.start = (
            beat2time(
                note_beat - previous_bpm_beat, 60000.0 / bpms[previous_bpm_index].bpm
            )
            + previous_time
        )
        end_beat = mc_note.get("endbeat", None)
        if end_beat != None:
            end_beat = Beat(*end_beat)
            temp_previous_bpm_index = previous_bpm_index
            temp_next_bpm_index = next_bpm_index
            temp_previous_time = previous_time
            while temp_next_bpm_index < len(bpms):
                temp_next_bpm_beat = Beat(*mc_map["time"][temp_next_bpm_index]["beat"])
                if end_beat >= temp_next_bpm_beat:
                    temp_previous_bpm_beat = Beat(
                        *mc_map["time"][temp_previous_bpm_index]["beat"]
                    )
                    temp_previous_time += beat2time(
                        temp_next_bpm_beat - temp_previous_bpm_beat,
                        60000.0 / bpms[temp_previous_bpm_index].bpm,
                    )
                    temp_previous_bpm_index += 1
                    temp_next_bpm_index += 1
                else:
                    break
            temp_previous_bpm_beat = Beat(
                *mc_map["time"][temp_previous_bpm_index]["beat"]
            )
            note.end = (
                beat2time(
                    end_beat - temp_previous_bpm_beat,
                    60000.0 / bpms[temp_previous_bpm_index].bpm,
                )
                + temp_previous_time
            )
        hitsound = mc_note.get("sound", None)
        if hitsound != None:
            note.hitsound = hitsound
            note.volumn = mc_note.get("vol", 100)
        notes.append(note)
    map.notes = notes
    map.audio = audio
    return map


def write_osu(map: ManiaMap, filename):
    file = open(filename, "w", encoding="utf-8")
    osu_data_file = open("osu_base.txt", "r", encoding="utf-8")
    osu_datas = osu_data_file.read()
    osu_data_file.close()
    osu_datas = osu_datas.format(
        audio=map.audio,
        leadin=map.leadin,
        preview=map.preview,
        title=map.title,
        title_unicode=map.title_unicode,
        artist=map.artist,
        artist_unicode=map.artist_unicode,
        creator=map.creator,
        version=map.version,
        key_amount=map.key_amount,
        background="",
    )
    file.write(osu_datas)
    file.write("\n[TimingPoints]\n")
    for bpm in map.bpms:
        file.write(f"{str(int(bpm.time))},{str(60000.0 / bpm.bpm)},4,1,1,100,1,0\n")
    file.write("\n\n\n[HitObjects]\n")
    column_width = 512 / map.key_amount
    for note in map.notes:
        if note.end > note.start:
            file.write(
                f"{str(int(note.column * column_width + column_width * 0.5))},192,{str(int(note.start))},128,0,{str(int(note.end))}:0:0:0:{str(int(note.volumn))}:{str(note.hitsound)}\n"
            )
        else:
            file.write(
                f"{str(int(note.column * column_width + column_width * 0.5))},192,{str(int(note.start))},1,0,{str(int(note.end))}:0:0:{str(int(note.volumn))}:{str(note.hitsound)}\n"
            )
    file.flush()


def write_mc(map: ManiaMap, filename):
    file = open(filename, "w", encoding="utf-8")
    mc = dict()
    mc["meta"] = dict()
    mc["meta"]["creator"] = map.creator
    mc["meta"]["version"] = map.version
    mc["meta"]["preview"] = map.preview
    mc["meta"]["mode"] = 0
    mc["meta"]["time"] = int(time.time())
    mc["meta"]["song"] = dict()
    mc["meta"]["song"]["title"] = map.title
    mc["meta"]["song"]["artist"] = map.artist
    mc["meta"]["mode_ext"] = dict()
    mc["meta"]["mode_ext"]["column"] = map.key_amount
    mc["meta"]["mode_ext"]["bar_begin"] = 0
    mc_time = []
    mc["time"] = mc_time
    previous_bpm_time = map.bpms[0].time
    previous_beat = Beat()
    previous_bpm = map.bpms[0].bpm
    mc_time.append(
        {
            "beat": [previous_beat.a, previous_beat.b, previous_beat.c],
            "bpm": previous_bpm,
        }
    )
    for bpm in map.bpms[1:]:
        r_time = bpm.time - previous_bpm_time
        r_beat = time2beat(r_time, 60000.0 / previous_bpm)
        previous_beat += r_beat
        previous_bpm = bpm.bpm
        previous_bpm_time = bpm.time
        mc_time.append(
            {
                "beat": [previous_beat.a, previous_beat.b, previous_beat.c],
                "bpm": previous_bpm,
            }
        )
    current_bpm_index = 0
    next_bpm_index = 1
    mc_note = []
    mc["note"] = mc_note
    for note in map.notes:
        while next_bpm_index < len(map.bpms):
            if map.bpms[next_bpm_index].time > note.start:
                break
            next_bpm_index += 1
            current_bpm_index += 1
        r_time = note.start - map.bpms[current_bpm_index].time
        r_beat = time2beat(r_time, 60000.0 / mc_time[current_bpm_index]["bpm"])
        s_beat = Beat(*mc_time[current_bpm_index]["beat"])
        s_beat += r_beat
        new_note = {"beat": [s_beat.a, s_beat.b, s_beat.c], "column": note.column}
        if note.end > note.start:
            temp_current_bpm_index = current_bpm_index
            temp_next_bpm_index = next_bpm_index
            while temp_next_bpm_index < len(map.bpms):
                if map.bpms[temp_next_bpm_index].time > note.end:
                    break
                temp_next_bpm_index += 1
                temp_current_bpm_index += 1
            r_time = note.end - map.bpms[temp_current_bpm_index].time
            r_beat = time2beat(r_time, 60000.0 / mc_time[temp_current_bpm_index]["bpm"])
            e_beat = Beat(*mc_time[temp_current_bpm_index]["beat"])
            e_beat += r_beat
            new_note["endbeat"] = [e_beat.a, e_beat.b, e_beat.c]
        if len(note.hitsound) > 0:
            new_note["sound"] = note.hitsound
            new_note["vol"] = note.volumn
        mc_note.append(new_note)
    mc_note.append(
        {
            "beat": [0, 0, 1],
            "sound": map.audio,
            "vol": 100,
            "offset": map.bpms[0].time,
            "type": 1,
        }
    )
    mc["extra"] = {
        "test": {"divide": 4, "speed": 100, "save": 0, "lock": 0, "edit_mode": 0}
    }
    strs = json.dumps(mc, ensure_ascii=False, indent=4)
    file.write(strs)
    file.close()


match_filename = r"(.+)\.(.+)"


def convert(filename):
    matched = re.match(match_filename, filename)
    if not matched:
        return
    name = matched.group(1)
    filetype = matched.group(2).lower()
    if filetype == "osu":
        write_mc(parse_osu(filename), name + ".mc")
    elif filetype == "mc":
        write_osu(parse_mc(filename), name + ".osu")


for index, arg in enumerate(sys.argv[1:]):
    print(f'({str(index+1)}/{str(len(sys.argv)-1)}) Converting "{arg}"')
    convert(arg)
    print("Complete~")

os.system("pause")

