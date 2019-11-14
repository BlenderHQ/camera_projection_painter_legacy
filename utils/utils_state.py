__all__ = ["state", "event"]


class TempDataStorage(object):
    __slots__ = (
        "operator",
        "tmp_camera"
    )

    def __init__(self):
        self.operator = None
        self.tmp_camera = None


class EventContainer(object):
    __slots__ = (
        "mouse_position",
        "type",
        "value",
        "ctrl",
        "shift",
        "alt",
    )

    def __init__(self):
        self.mouse_position = (0, 0)
        self.type = None
        self.value = None
        self.ctrl = False
        self.shift = False
        self.alt = False


state = TempDataStorage()
event = EventContainer()
