from datetime import timedelta


class Time():
    def __init__(self, delta: timedelta):
        self._delta = delta

    @property
    def formatted_hour_min_sec(self) -> str:
        hour = self._delta.seconds//3600
        minute = (self._delta.seconds//60) % 60
        second = self._delta.seconds - (hour*3600 + minute*60)
        return "%02d:%02d:%02d" % (hour, minute, second)
