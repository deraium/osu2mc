import osu_mania
import mania
import sys


def convert(filename, base_bpm):
    chart = osu_mania.parse(filename, True)
    for bpm in chart.bpms:
        chart.effects.append(mania.Effect(bpm.time, bpm.bpm / base_bpm))
    chart.effects.sort(key=lambda x: x.time)
    chart.bpms = [mania.BPM(time=chart.bpms[0].time, bpm=base_bpm)]
    chart.version = f"{chart.version} (Green)"
    osu_mania.write(
        chart, f"{chart.artist} - {chart.title} ({chart.creator}) [{chart.version}].osu"
    )


convert(sys.argv[1], float(sys.argv[2]))

