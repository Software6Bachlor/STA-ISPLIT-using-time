def test_loadAndParse_chainSta():
    from loader import loadData
    from parser import parseModel
    from models.STA import UnaryExpression, VariableReference

    # Arrange
    path = "models/benchmark/jani/chain-sta.jani"

    # Act
    data = loadData(path)
    model = parseModel(data)

    # Assert — model identity
    assert model.name == "chain-sta"
    assert model.type == "sta"
    # Assert — structure
    assert len(model.automata) == 1
    assert model.automata[0].name == "Chain"
    assert len(model.constants) == 4
    assert [c.name for c in model.constants] == ["N", "FAIL_W", "PASS_W", "TIME_BOUND"]
    assert len(model.variables) == 2
    assert [v.name for v in model.variables] == ["gate", "failure"]
    assert len(model.properties) == 1
    assert model.properties[0].name == "P_Failure"
    # Assert — property expression fully parsed (no raw strings or None)
    f_expr = model.properties[0].expression.operands["values"].operands["exp"]
    assert f_expr.op == "F"
    assert isinstance(f_expr.operands["exp"], VariableReference)
    assert f_expr.operands["exp"].name == "failure"
    assert f_expr.operands["time-bounds"]["upper"].name == "TIME_BOUND"
    assert model.properties[0].expression.operands["states"].op == "initial"
    assert len(model.automata[0].edges) == 4
    # Assert — destination probability parsed (PASS_W / (PASS_W + FAIL_W))
    first_dest = model.automata[0].edges[0].destinations[0]
    assert first_dest.probability is not None
    assert first_dest.probability.op == "/"
    # Assert — unary ¬ operator parsed correctly in edge guard
    guard = model.automata[0].edges[0].guard
    assert isinstance(guard.right, UnaryExpression)
    assert guard.right.op == "¬"
    assert guard.right.exp.name == "failure"


def test_loadAndParse_longSta():
    from loader import loadData
    from parser import parseModel
    from models.STA import Distribution

    # Arrange
    path = "models/benchmark/jani/long-sta.jani"

    # Act
    data = loadData(path)
    model = parseModel(data)

    # Assert — model identity
    assert model.name == "long-sta"
    assert model.type == "sta"
    # Assert — structure
    assert len(model.automata) == 1
    assert model.automata[0].name == "STop"
    assert len(model.constants) == 3
    assert [c.name for c in model.constants] == ["RARE_LO", "Y_THRESHOLD", "TIME_BOUND"]
    assert len(model.variables) == 2
    assert [v.name for v in model.variables] == ["acy", "rare_event"]
    assert len(model.properties) == 1
    assert model.properties[0].name == "P_Rare"
    assert len(model.automata[0].edges) == 5
    # Assert — variable x initial-value is a parsed Distribution, not a raw dict
    var_x = next(v for v in model.automata[0].variables if v.name == "x")
    assert isinstance(var_x.initial_value, Distribution)
    assert var_x.initial_value.type == "Uniform"
    # Assert — loc_0 has no time-progress invariant (absorbing location)
    loc0 = next(loc for loc in model.automata[0].locations if loc.name == "loc_0")
    assert loc0.timeProgress is None


def test_loadAndParse_manufacturingSta():
    from loader import loadData
    from parser import parseModel

    # Arrange
    path = "models/benchmark/jani/manufacturing-sta.jani"

    # Act
    data = loadData(path)
    model = parseModel(data)

    # Assert — model identity
    assert model.name == "manufacturing-sta"
    assert model.type == "sta"
    # Assert — structure
    assert len(model.automata) == 1
    assert model.automata[0].name == "Idle"
    assert len(model.constants) == 3
    assert [c.name for c in model.constants] == ["TIME_BOUND", "PASS_W", "FAIL_W"]
    assert len(model.variables) == 3
    assert [v.name for v in model.variables] == ["acycle", "uptime", "failure"]
    assert len(model.properties) == 1
    assert model.properties[0].name == "P_Failure"
    assert len(model.automata[0].edges) == 9
    # Assert — loc_0 has no time-progress invariant (absorbing location)
    loc0 = next(loc for loc in model.automata[0].locations if loc.name == "loc_0")
    assert loc0.timeProgress is None


def test_loadAndParse_tandemQueue():
    from loader import loadData
    from parser import parseModel

    # Arrange
    path = "models/benchmark/jani/tandem-queue.jani"

    # Act
    data = loadData(path)
    model = parseModel(data)

    # Assert — model identity
    assert model.name == "tandem-queue"
    assert model.type == "sta"
    # Assert — structure (3 parallel automata)
    assert len(model.automata) == 3
    assert [a.name for a in model.automata] == ["Arrivals", "ServerC", "ServerM"]
    assert len(model.constants) == 2
    assert [c.name for c in model.constants] == ["TIME_BOUND", "SCALE"]
    assert len(model.variables) == 2
    assert [v.name for v in model.variables] == ["q1", "q2"]
    assert len(model.properties) == 4
    assert [p.name for p in model.properties] == ["PAllFull", "PFirstFull", "EAllFull", "EFirstFull"]
