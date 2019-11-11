__all__ = ["state"]


class TempDataStorage(object):
    __slots__ = (
        "operator",
        "tmp_camera",
    )

    def __init__(self):
        self.operator = None
        self.tmp_camera = None


state = TempDataStorage()
