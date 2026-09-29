from datetime import datetime


class TimeCore:
    """Provides the current local date and time from the operating system."""

    @staticmethod
    def get_datetime():
        now = datetime.now().astimezone()

        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.isoformat(timespec="seconds"),
        }