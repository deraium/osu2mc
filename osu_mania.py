import re
import mania

match_item = r"(.+?): *(.+)"
match_section = r"[\t ]*\[(.+)\][\t ]*"
match_bpm = r"[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*"
match_note = r"[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*,[\t ]*(.+?)[\t ]*:[\t ]*(.+)[\t ]*"
match_hitsound = r"(?:.+:)*(.+):(.*)"


def parse(filename, remove_green_line=False):
    file = open(filename, "r", encoding="utf-8")
    chart = mania.Chart()
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
                    chart.audio = value
                elif attribute == "AudioLeadIn":
                    chart.leadin = value
                elif attribute == "PreviewTime":
                    chart.preview = value
                elif attribute == "Title":
                    chart.title = value
                elif attribute == "TitleUnicode":
                    chart.title_unicode = value
                elif attribute == "Artist":
                    chart.artist = value
                elif attribute == "ArtistUnicode":
                    chart.artist_unicode = value
                elif attribute == "Creator":
                    chart.creator = value
                elif attribute == "Version":
                    chart.version = value
                elif attribute == "CircleSize":
                    chart.key_amount = int(value)
            continue
        if section == "TimingPoints":
            matched = re.match(match_bpm, line)
            if matched:
                bpm = mania.BPM()
                bpm.time = float(matched.group(1))
                bpm.bpm = float(matched.group(2))
                if bpm.bpm > 0:
                    bpm.bpm = mania.accu_bpm(60000.0 / bpm.bpm)
                    previous_bpm = bpm.bpm
                    chart.bpms.append(bpm)
                    if not remove_green_line:
                        chart.effects.append(mania.Effect(bpm.time))
                else:
                    if remove_green_line:
                        previous_bpm_index = len(chart.bpms) - 1
                        if bpm.time == chart.bpms[previous_bpm_index].time:
                            chart.bpms[previous_bpm_index].bpm = mania.accu_bpm(
                                -100.0 / bpm.bpm * previous_bpm
                            )
                        else:
                            bpm.bpm = mania.accu_bpm(-100.0 / bpm.bpm * previous_bpm)
                            chart.bpms.append(bpm)
                    else:
                        effect = mania.Effect(bpm.time, -100.0 / bpm.bpm)
                        chart.effects.append(effect)
            continue
        if section == "HitObjects":
            matched = re.match(match_note, line)
            if matched:
                note = mania.Note()
                note.column = int(int(matched.group(1)) / 512 * chart.key_amount)
                note.start = float(matched.group(3))
                note.end = float(matched.group(6))
                extras = matched.group(7)
                extra_matched = re.match(match_hitsound, extras)
                if extra_matched:
                    hitsound_file = extra_matched.group(2)
                    if len(hitsound_file) > 0:
                        note.hitsound = hitsound_file
                        note.volumn = float(extra_matched.group(1))
                chart.notes.append(note)
    file.close()
    return chart


def write(chart: mania.Chart, filename):
    file = open(filename, "w", encoding="utf-8")
    osu_data_file = open("osu_mania_base.txt", "r", encoding="utf-8")
    osu_datas = osu_data_file.read()
    osu_data_file.close()
    osu_datas = osu_datas.format(
        audio=chart.audio,
        leadin=chart.leadin,
        preview=chart.preview,
        title=chart.title,
        title_unicode=chart.title_unicode,
        artist=chart.artist,
        artist_unicode=chart.artist_unicode,
        creator=chart.creator,
        version=chart.version,
        key_amount=chart.key_amount,
        background="",
    )
    file.write(osu_datas)
    file.write("\n[TimingPoints]\n")
    osu_bpm_list = chart.bpms.copy()
    for effect in chart.effects:
        if effect.scroll > 0.0:
            osu_bpm_list.append(mania.BPM(effect.time, -100.0 / effect.scroll))
        else:
            osu_bpm_list.append(mania.BPM(effect.time, -1000000))
    osu_bpm_list.sort(key=lambda x: x.time)
    for bpm in osu_bpm_list:
        if bpm.bpm > 0:
            file.write(f"{str(int(bpm.time))},{str(60000.0 / bpm.bpm)},4,1,1,100,1,0\n")
        elif bpm.bpm < 0:
            file.write(f"{str(int(bpm.time))},{str(bpm.bpm)},4,1,1,100,0,0\n")
        else:
            file.write(f"{str(int(bpm.time))},999999999,4,1,1,100,1,0\n")
    file.write("\n\n\n[HitObjects]\n")
    column_width = 512 / chart.key_amount
    for note in chart.notes:
        if note.end > note.start:
            file.write(
                f"{str(int(note.column * column_width + column_width * 0.5))},192,{str(int(note.start))},128,0,{str(int(note.end))}:0:0:0:{str(int(note.volumn))}:{str(note.hitsound)}\n"
            )
        else:
            file.write(
                f"{str(int(note.column * column_width + column_width * 0.5))},192,{str(int(note.start))},1,0,{str(int(note.end))}:0:0:{str(int(note.volumn))}:{str(note.hitsound)}\n"
            )
    file.flush()
