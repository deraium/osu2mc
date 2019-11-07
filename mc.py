from beat import Beat
import mania
import time
import json


def parse(filename):
    file = open(filename, "r", encoding="utf-8")
    chart = mania.Chart()
    json_datas = file.read()
    mc_chart = json.loads(json_datas)
    chart.artist = mc_chart["meta"]["song"]["artist"]
    chart.artist_unicode = mc_chart["meta"]["song"]["artist"]
    chart.creator = mc_chart["meta"]["creator"]
    chart.key_amount = mc_chart["meta"]["mode_ext"]["column"]
    chart.leadin = 0
    chart.preview = mc_chart["meta"].get("preview", 0)
    chart.title = mc_chart["meta"]["song"]["title"]
    chart.title_unicode = mc_chart["meta"]["song"]["title"]
    chart.version = mc_chart["meta"]["version"]
    time_start = 0.0
    audio = ""
    note_special = mc_chart["note"][0]
    if note_special.get("type", 0) == 1:
        time_start = note_special["offset"]
        audio = note_special["sound"]
    else:
        note_special = mc_chart["note"][-1]
        if note_special.get("type", 0) == 1:
            time_start = note_special["offset"]
            audio = note_special["sound"]
        else:
            for mc_note in mc_chart["note"][1:-1]:
                if mc_note.get("type", 0) == 1:
                    time_start = mc_note["offset"]
                    audio = mc_note["sound"]
                    break
    bpms = []
    previous_time = time_start
    previous_bpm = 200.0
    previous_beat = Beat()
    for mc_bpm in mc_chart["time"]:
        bpm = mania.BPM()
        beat = Beat(*mc_bpm["beat"])
        bpm.time = previous_time + (beat - previous_beat).to_time(
            60000.0 / previous_bpm
        )
        bpm.bpm = mc_bpm["bpm"]
        bpms.append(bpm)
        previous_time = bpm.time
        previous_bpm = bpm.bpm
        previous_beat = beat
    chart.bpms = bpms
    notes = []
    previous_bpm_index = 0
    next_bpm_index = 1
    previous_time = time_start
    for mc_note in mc_chart["note"]:
        column = mc_note.get("column", None)
        if column == None:
            continue
        note_beat = Beat(*mc_note["beat"])
        while next_bpm_index < len(bpms):
            next_bpm_beat = Beat(*mc_chart["time"][next_bpm_index]["beat"])
            if note_beat >= next_bpm_beat:
                previous_bpm_beat = Beat(*mc_chart["time"][previous_bpm_index]["beat"])
                previous_time += (next_bpm_beat - previous_bpm_beat).to_time(
                    60000.0 / bpms[previous_bpm_index].bpm
                )
                previous_bpm_index += 1
                next_bpm_index += 1
            else:
                break
        previous_bpm_beat = Beat(*mc_chart["time"][previous_bpm_index]["beat"])
        note = mania.Note()
        note.column = column
        note.start = (note_beat - previous_bpm_beat).to_time(
            60000.0 / bpms[previous_bpm_index].bpm
        ) + previous_time
        end_beat = mc_note.get("endbeat", None)
        if end_beat != None:
            end_beat = Beat(*end_beat)
            temp_previous_bpm_index = previous_bpm_index
            temp_next_bpm_index = next_bpm_index
            temp_previous_time = previous_time
            while temp_next_bpm_index < len(bpms):
                temp_next_bpm_beat = Beat(
                    *mc_chart["time"][temp_next_bpm_index]["beat"]
                )
                if end_beat >= temp_next_bpm_beat:
                    temp_previous_bpm_beat = Beat(
                        *mc_chart["time"][temp_previous_bpm_index]["beat"]
                    )
                    temp_previous_time += (
                        temp_next_bpm_beat - temp_previous_bpm_beat
                    ).to_time(60000.0 / bpms[temp_previous_bpm_index].bpm)
                    temp_previous_bpm_index += 1
                    temp_next_bpm_index += 1
                else:
                    break
            temp_previous_bpm_beat = Beat(
                *mc_chart["time"][temp_previous_bpm_index]["beat"]
            )
            note.end = (end_beat - temp_previous_bpm_beat).to_time(
                60000.0 / bpms[temp_previous_bpm_index].bpm
            ) + temp_previous_time
        hitsound = mc_note.get("sound", None)
        if hitsound != None:
            note.hitsound = hitsound
            note.volume = mc_note.get("vol", 100)
        notes.append(note)
    chart.notes = notes
    chart.audio = audio
    effects = mc_chart.get("effect", None)
    if effects:
        previous_bpm_index = 0
        next_bpm_index = 1
        previous_time = time_start
        for mc_effect in effects:
            beat = Beat(*mc_effect["beat"])
            scroll = mc_effect["scroll"]
            while next_bpm_index < len(bpms):
                next_bpm_beat = Beat(*mc_chart["time"][next_bpm_index]["beat"])
                if beat >= next_bpm_beat:
                    previous_bpm_beat = Beat(
                        *mc_chart["time"][previous_bpm_index]["beat"]
                    )
                    previous_time += (next_bpm_beat - previous_bpm_beat).to_time(
                        60000.0 / bpms[previous_bpm_index].bpm
                    )
                    previous_bpm_index += 1
                    next_bpm_index += 1
                else:
                    break
            previous_bpm_beat = Beat(*mc_chart["time"][previous_bpm_index]["beat"])
            effect = mania.Effect(
                time=(beat - previous_bpm_beat).to_time(
                    60000.0 / bpms[previous_bpm_index].bpm
                )
                + previous_time,
                scroll=scroll,
            )
            chart.effects.append(effect)
    return chart


def write(chart: mania.Chart, filename):
    file = open(filename, "w", encoding="utf-8")
    mc = dict()
    mc["meta"] = dict()
    mc["meta"]["creator"] = chart.creator
    mc["meta"]["version"] = chart.version
    mc["meta"]["preview"] = chart.preview
    mc["meta"]["mode"] = 0
    mc["meta"]["time"] = int(time.time())
    mc["meta"]["song"] = dict()
    mc["meta"]["song"]["title"] = chart.title
    mc["meta"]["song"]["artist"] = chart.artist
    mc["meta"]["mode_ext"] = dict()
    mc["meta"]["mode_ext"]["column"] = chart.key_amount
    mc["meta"]["mode_ext"]["bar_begin"] = 0
    mc_time = []
    mc["time"] = mc_time
    previous_bpm_time = chart.bpms[0].time
    previous_beat = Beat()
    previous_bpm = chart.bpms[0].bpm
    mc_time.append(
        {
            "beat": [previous_beat.a, previous_beat.b, previous_beat.c],
            "bpm": previous_bpm,
        }
    )
    for bpm in chart.bpms[1:]:
        r_time = bpm.time - previous_bpm_time
        r_beat = Beat.from_time(r_time, 60000.0 / previous_bpm)
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
    mc_effects = []
    mc["effect"] = mc_effects
    for effect in chart.effects:
        while next_bpm_index < len(chart.bpms):
            if chart.bpms[next_bpm_index].time > effect.time:
                break
            current_bpm_index += 1
            next_bpm_index += 1
        r_time = effect.time - chart.bpms[current_bpm_index].time
        r_beat = Beat.from_time(r_time, 60000.0 / mc_time[current_bpm_index]["bpm"])
        beat = Beat(*mc_time[current_bpm_index]["beat"])
        beat += r_beat
        mc_effect = {"beat": [beat.a, beat.b, beat.c], "scroll": effect.scroll}
        mc_effects.append(mc_effect)
    current_bpm_index = 0
    next_bpm_index = 1
    mc_note = []
    mc["note"] = mc_note
    for note in chart.notes:
        while next_bpm_index < len(chart.bpms):
            if chart.bpms[next_bpm_index].time > note.start:
                break
            next_bpm_index += 1
            current_bpm_index += 1
        r_time = note.start - chart.bpms[current_bpm_index].time
        r_beat = Beat.from_time(r_time, 60000.0 / mc_time[current_bpm_index]["bpm"])
        s_beat = Beat(*mc_time[current_bpm_index]["beat"])
        s_beat += r_beat
        new_note = {"beat": [s_beat.a, s_beat.b, s_beat.c], "column": note.column}
        if note.end > note.start:
            temp_current_bpm_index = current_bpm_index
            temp_next_bpm_index = next_bpm_index
            while temp_next_bpm_index < len(chart.bpms):
                if chart.bpms[temp_next_bpm_index].time > note.end:
                    break
                temp_next_bpm_index += 1
                temp_current_bpm_index += 1
            r_time = note.end - chart.bpms[temp_current_bpm_index].time
            r_beat = Beat.from_time(
                r_time, 60000.0 / mc_time[temp_current_bpm_index]["bpm"]
            )
            e_beat = Beat(*mc_time[temp_current_bpm_index]["beat"])
            e_beat += r_beat
            new_note["endbeat"] = [e_beat.a, e_beat.b, e_beat.c]
        if len(note.hitsound) > 0:
            new_note["sound"] = note.hitsound
            new_note["vol"] = note.volume
        mc_note.append(new_note)
    mc_note.append(
        {
            "beat": [0, 0, 1],
            "sound": chart.audio,
            "vol": 100,
            "offset": chart.bpms[0].time,
            "type": 1,
        }
    )
    mc["extra"] = {
        "test": {"divide": 4, "speed": 100, "save": 0, "lock": 0, "edit_mode": 0}
    }
    strs = json.dumps(mc, ensure_ascii=False, indent=4)
    file.write(strs)
    file.close()
