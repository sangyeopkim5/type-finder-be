import pathlib, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

import pytest
from apps.cas.compute import run_cas
from libs.schemas import CASJob


def test_run_cas_operations():
    jobs = [
        CASJob(id="s1", expr="sin(pi/2)"),
        CASJob(id="s2", expr="expand((x+1)**2)"),
        CASJob(id="s3", expr="sqrt(4)")
    ]
    res = run_cas(jobs)
    assert res[0].result_py == "1"
    assert "x**2 + 2*x + 1" in res[1].result_py
    assert res[2].result_py == "2"


def test_run_cas_error():
    with pytest.raises(ValueError) as e:
        run_cas([CASJob(id="bad", expr="badfunc(1)")])
    assert "bad" in str(e.value)
