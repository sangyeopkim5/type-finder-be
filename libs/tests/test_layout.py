import pathlib, sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from libs.layout import reading_order


class Obj:
    def __init__(self, bbox):
        self.bbox = bbox


def test_reading_order_basic():
    a = Obj([0, 0, 10, 10])
    b = Obj([20, 0, 30, 10])
    c = Obj([5, 15, 15, 25])
    ordered = reading_order([b, c, a])
    assert ordered == [a, b, c]


def test_reading_order_small_offsets():
    a = Obj([0, 0, 10, 10])
    b = Obj([12, 2, 22, 12])  # small vertical offset, same row
    c = Obj([0, 20, 10, 30])
    ordered = reading_order([b, c, a])
    assert ordered == [a, b, c]


def test_reading_order_tiebreakers():
    a = Obj([0, 0, 10, 10])
    b = Obj([0, 0, 8, 8])
    c = Obj([0, -2, 10, 8])
    ordered = reading_order([a, b, c])
    assert ordered == [c, b, a]
