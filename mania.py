class Note(object):
    def __init__(self):
        self.start = 0.0
        self.end = 0.0
        self.column = 0
        self.hitsound = ""
        self.volume = 0


class BPM(object):
    def __init__(self, time=0, bpm=222.22):
        self.time = time
        self.bpm = bpm


class Effect(object):
    def __init__(self, time=0, scroll=1.0):
        self.time = time
        self.scroll = scroll


class Chart(object):
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
        self.effects = []


def accu_bpm(bpm: float, precision: float = 0.001, limit: int = 8):
    origin_bpm = bpm
    for i in range(0, limit):
        if abs(bpm - int(bpm + 0.5)) < precision:
            return int(bpm) / (10 ** i)
        bpm *= 10.0
    return origin_bpm
