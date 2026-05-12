import dataclasses
import pytest

from models.STA import BinaryExpression, Literal, VariableReference


def _load_model():
    from loader import loadData
    from parser import parseModel
    data = loadData("tests/testData/manufacturing-sta.jani")
    model = parseModel(data)
    consts_map = {"TIME_BOUND": 100.0, "PASS_W": 1, "FAIL_W": 1}
    new_consts = tuple(
        dataclasses.replace(c, value=consts_map[c.name]) for c in model.constants
    )
    return dataclasses.replace(model, constants=new_consts)


# ── _evaluateRareEvent ───────────────────────────────────────────────

@pytest.mark.parametrize("expr,globalVars,expected", [
    (VariableReference("failure"), {"failure": 1.0},  True),
    (VariableReference("failure"), {"failure": 0.0},  False),
    (Literal(True),                {},                True),
    (Literal(False),               {},                False),
    (BinaryExpression("∧", VariableReference("a"), VariableReference("b")), {"a": 1.0, "b": 1.0}, True),
    (BinaryExpression("∧", VariableReference("a"), VariableReference("b")), {"a": 1.0, "b": 0.0}, False),
    (BinaryExpression("=",  VariableReference("x"), Literal(3)), {"x": 3},  True),
    (BinaryExpression("=",  VariableReference("x"), Literal(3)), {"x": 5},  False),
    (BinaryExpression("∨",  Literal(True), Literal(True)), {},              False),
], ids=[
    "varref-true", "varref-false",
    "literal-true", "literal-false",
    "and-both-true", "and-one-false",
    "equality-match", "equality-mismatch",
    "unsupported-or-returns-false",
])
def test_evaluateRareEvent(expr, globalVars, expected):
    from loader import loadData
    from parser import parseModel
    from models.simulation import MonteCarloSimulation
    from models.state import State

    model = parseModel(loadData("tests/testData/manufacturing-sta.jani"))
    sim = MonteCarloSimulation(model, numTrials=1, timeBound=1.0)
    state = State(locations={}, globalVars=globalVars, autoVars={})

    assert sim._evaluateRareEvent(expr, state) == expected


# ── Constructor ──────────────────────────────────────────────────────

def test_init_extractsRareEventExpr():
    from loader import loadData
    from parser import parseModel
    from models.simulation import MonteCarloSimulation

    model = parseModel(loadData("tests/testData/manufacturing-sta.jani"))
    sim = MonteCarloSimulation(model, numTrials=1, timeBound=1.0)

    assert isinstance(sim._rareEventExpr, VariableReference)
    assert sim._rareEventExpr.name == "failure"


def test_init_raisesOnNoProperty():
    from loader import loadData
    from parser import parseModel
    from models.simulation import MonteCarloSimulation

    model = parseModel(loadData("tests/testData/manufacturing-sta.jani"))
    model_no_props = dataclasses.replace(model, properties=())

    with pytest.raises(ValueError):
        MonteCarloSimulation(model_no_props, numTrials=1, timeBound=1.0)


# ── Group 3: run() result shape ───────────────────────────────────────────────

def test_run_zeroTrials():
    from models.simulation import MonteCarloSimulation, MonteCarloResult

    result = MonteCarloSimulation(_load_model(), numTrials=0, timeBound=1.0).run()

    assert isinstance(result, MonteCarloResult)
    assert result.probabilityEstimate == 0.0
    assert result.numHits == 0
    assert result.ciContainsZero is True


def test_run_returnsMonteCarloResult():
    from models.simulation import MonteCarloSimulation, MonteCarloResult

    result = MonteCarloSimulation(_load_model(), numTrials=10, timeBound=0.0).run()

    assert isinstance(result, MonteCarloResult)


def test_run_numHitsWithinBounds():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=10, timeBound=0.0).run()

    assert 0 <= result.numHits <= result.numTrials


def test_run_probabilityEstimateMatchesRatio():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=10, timeBound=0.0).run()

    assert result.probabilityEstimate == result.numHits / result.numTrials


# ── Group 4: Wilson CI correctness ───────────────────────────────────────────

def test_run_zeroHits_ciContainsZeroTrue():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=100, timeBound=0.0).run()

    assert result.numHits == 0
    assert result.ciContainsZero is True


def test_run_zeroHits_halfWidthPositive():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=100, timeBound=0.0).run()

    assert result.halfWidth > 0


# ── writeResult() JSON output ─────────────────────────────────────────────────

def test_writeResult_createsJsonWithMcFields(tmp_path, monkeypatch):
    import json
    import containerMain
    from models.simulation import MonteCarloResult

    monkeypatch.setattr(containerMain, "RESULTS_DIR", str(tmp_path))

    model = _load_model()
    result = MonteCarloResult(
        probabilityEstimate=0.005,
        halfWidth=0.001,
        ciContainsZero=False,
        numTrials=1000,
        numHits=5,
    )

    containerMain.writeResult("some/path/manufacturing-sta.jani", model, 100.0, result)

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))

    assert payload["modelName"] == "manufacturing-sta"
    assert payload["method"] == "CMC"
    assert payload["timeBound"] == 100.0
    assert payload["numTrials"] == 1000
    assert payload["numHits"] == 5
    assert payload["probabilityEstimate"] == 0.005
    assert payload["halfWidth"] == 0.001
    assert payload["ciContainsZero"] is False
    assert "generatedAtUtc" in payload
