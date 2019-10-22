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
        return self.reduction()

    def __sub__(self, beat_2):
        beat = Beat()
        beat.a = self.a - beat_2.a
        beat.b = self.b * beat_2.c - self.c * beat_2.b
        beat.c = self.c * beat_2.c
        return beat.reduction()

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

    @staticmethod
    def from_time(time: float, millseconds_per_beat: float, max_error: float = 1.0):
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
        return Beat(a, b, c)

    def to_time(self, millseconds_per_beat: float):
        return (self.a + (self.b / self.c)) * millseconds_per_beat
