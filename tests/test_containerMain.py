import json

import pytest

import containerMain

pytestmark = pytest.mark.skip(reason="Tests not up to date - needs update")

def test_parseModelPathArg_missing_raisesSystemExit():
    with pytest.raises(SystemExit) as error:
        containerMain.parseModelPathArg(["containerMain.py"])

    assert error.value.code == 1


def test_parseModelPathArg_invalidPath_raisesSystemExit(tmp_path):
    missing = tmp_path / "missing.jani"

    with pytest.raises(SystemExit) as error:
        containerMain.parseModelPathArg(["containerMain.py", str(missing)])

    assert error.value.code == 1


def test_parseModelPathArg_validPath_returnsPath(tmp_path):
    model = tmp_path / "model.jani"
    model.write_text("{}", encoding="utf-8")

    value = containerMain.parseModelPathArg(["containerMain.py", str(model)])
    assert value == str(model)
