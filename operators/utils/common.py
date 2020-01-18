# <pep8 compliant>

class PropertyTracker(object):
    __slots__ = ("value",)

    def __init__(self, value = None):
        self.value = value

    def __call__(self, value = None):
        if self.value != value:
            self.value = value
            return True
        return False


# Math
def f_clamp(value: float, min_value: float, max_value: float):
    """Clamp float value"""
    return max(min(value, max_value), min_value)


def f_lerp(value0: float, value1: float, factor: float):
    """Linear interpolate float value"""
    return (value0 * (1.0 - factor)) + (value1 * factor)
