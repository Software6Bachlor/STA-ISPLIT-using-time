import pytest
import math

from DMB import DMB
from importanceFunctionBuilder import ImportanceFunctionBuilder
from models.clock import Clock
from models.stateSnapshot import StateSnapShot
from models.STA import (
    Location,
    Edge,
    Literal,
    Destination,
    Automaton,
    BinaryExpression,
    VariableReference,
    Variable,
    Assignment,
    Distribution,
)
from models.stateClass import StateClass


LARGE_DISTANCE = int(1e9)


@pytest.fixture
def simpleLinearAutomaton():
    """A -> B -> C"""
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    loc_b = Location(name="B", timeProgress=Literal(value=True))
    loc_c = Location(name="C", timeProgress=Literal(value=True))
    return Automaton(
        name="simpleLinear",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guard=Literal(value=True), destinations=[Destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guard=Literal(value=True), destinations=[Destination(location=loc_c, assignments=[])]),
        ])

@pytest.fixture
def branchingAutomaton():
    """A -> B, A -> C"""
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    loc_b = Location(name="B", timeProgress=Literal(value=True))
    loc_c = Location(name="C", timeProgress=Literal(value=True))

    return Automaton(
        name="branching",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guard=Literal(value=True), destinations=[
                Destination(location=loc_b, assignments=[]),
                Destination(location=loc_c, assignments=[])
            ]),
        ])

@pytest.fixture
def diamondAutomaton():
    """A -> B, A -> C, B -> D, C -> D"""
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    loc_b = Location(name="B", timeProgress=Literal(value=True))
    loc_c = Location(name="C", timeProgress=Literal(value=True))
    loc_d = Location(name="D", timeProgress=Literal(value=True))

    return Automaton(
        name="diamond",
        locations=[loc_a, loc_b, loc_c, loc_d],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guard=Literal(value=True), destinations=[
                Destination(location=loc_b, assignments=[]),
                Destination(location=loc_c, assignments=[])
            ]),
            Edge(location=loc_b, guard=Literal(value=True), destinations=[Destination(location=loc_d, assignments=[])]),
            Edge(location=loc_c, guard=Literal(value=True), destinations=[Destination(location=loc_d, assignments=[])]),
        ])

@pytest.fixture
def cyclicAutomaton():
    """A -> B -> C -> A"""
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    loc_b = Location(name="B", timeProgress=Literal(value=True))
    loc_c = Location(name="C", timeProgress=Literal(value=True))

    return Automaton(
        name="cyclic",
        locations=[loc_a, loc_b, loc_c],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(location=loc_a, guard=Literal(value=True), destinations=[Destination(location=loc_b, assignments=[])]),
            Edge(location=loc_b, guard=Literal(value=True), destinations=[Destination(location=loc_c, assignments=[])]),
            Edge(location=loc_c, guard=Literal(value=True), destinations=[Destination(location=loc_a, assignments=[])]),
        ])

# region Tests for hopDistanceDictBuilder
def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromC(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from C"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 0

def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromB(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from B"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result

def test_HopDistanceDictBuilder_SimpleLinearAutomatonFromA(simpleLinearAutomaton):
    """Verify distances in a simple linear Automaton A -> B -> C Starting from A"""
    # Arrange
    automaton: Automaton = simpleLinearAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result

def test_HopDistanceDictBuilder_BranchingAutomatonFromC(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert "B" not in result
    assert result["C"] == 0

def test_HopDistanceDictBuilder_BranchingAutomatonFromB(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result

def test_HopDistanceDictBuilder_BranchingAutomatonFromA(branchingAutomaton):
    """Verify distances for branches A -> B, A -> C"""
    # Arrange
    automaton: Automaton = branchingAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromA(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert "B" not in result
    assert "C" not in result
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromB(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromC(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert "B" not in result
    assert result["C"] == 0
    assert "D" not in result

def test_HopDistanceDictBuilder_DiamondAutomatonFromD(diamondAutomaton):
    """Verify shortest path in diamond Automaton"""
    # Arrange
    automaton: Automaton = diamondAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[3], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 1
    assert result["D"] == 0

def test_HopDistanceDictBuilder_CyclicAutomatonFromA(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[0], automaton.edges)

    # Assert
    assert result["A"] == 0
    assert result["B"] == 2
    assert result["C"] == 1

def test_HopDistanceDictBuilder_CyclicAutomatonFromB(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[1], automaton.edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert result["C"] == 2

def test_HopDistanceDictBuilder_CyclicAutomatonFromC(cyclicAutomaton):
    """Verify BFS handles cycles correctly without infinite loops"""
    # Arrange
    automaton: Automaton = cyclicAutomaton

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(automaton.locations[2], automaton.edges)

    # Assert
    assert result["A"] == 2
    assert result["B"] == 1
    assert result["C"] == 0

def test_HopDistanceDictBuilder_SingleNode():
    """Verify single isolated node returns distance 0"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    start = loc_a
    edges = []

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(start, edges)

    # Assert
    assert result["A"] == 0
    assert len(result) == 1

def test_HopDistanceDictBuilder_DisconnectedAutomaton():
    """Verify unreachable nodes are not included in result"""
    # Arrange
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    loc_b = Location(name="B", timeProgress=Literal(value=True))
    loc_c = Location(name="C", timeProgress=Literal(value=True))

    start = loc_b
    edges = [
        Edge(location=loc_a, guard=Literal(value=True), destinations=[Destination(location=loc_b, assignments=[])]),
    ]

    # Act
    result = ImportanceFunctionBuilder._hopDistanceDictBuilder(start, edges)

    # Assert
    assert result["A"] == 1
    assert result["B"] == 0
    assert "C" not in result
# endregion

# region Tests for timeDistanceDictBuilder and itsa helper functions

def test_applyComparisonConstraint_variableLessEqualLiteral():
    # Arrange
    dmb = DMB(["x"])

    # Act
    ImportanceFunctionBuilder._applyComparisonConstraint(dmb, VariableReference("x"), Literal(10), "<=")

    # Assert
    x_idx = dmb.clocks.index("x")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[x_idx][zero_idx] == 10


def test_applyComparisonConstraint_literalLessEqualVariable():
    # Arrange
    dmb = DMB(["x"])

    # Act
    ImportanceFunctionBuilder._applyComparisonConstraint(dmb, Literal(5), VariableReference("x"), "<=")

    # Assert
    x_idx = dmb.clocks.index("x")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[zero_idx][x_idx] == -5


def test_applyComparisonConstraint_invalidOperandsRaises():
    # Arrange
    dmb = DMB(["x"])

    # Act + Assert
    with pytest.raises(ValueError, match="Unsupported operands"):
        ImportanceFunctionBuilder._applyComparisonConstraint(dmb, Literal(1), Literal(2), "<=")


def test_applyConstraintExpressionToDMB_strictLessLogsWarning(caplog):
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression("<", VariableReference("x"), Literal(10))

    # Act
    with caplog.at_level("WARNING"):
        result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])

    # Assert
    x_idx = result[0].clocks.index("x")
    zero_idx = result[0].clocks.index("0")
    assert result[0].M[x_idx][zero_idx] == 10
    assert caplog.messages == []


def test_applyConstraintExpressionToDMB_strictLessLiteralVarLogsWarning(caplog):
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression("<", Literal(5), VariableReference("x"))

    # Act
    with caplog.at_level("WARNING"):
        result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])

    # Assert
    x_idx = result[0].clocks.index("x")
    zero_idx = result[0].clocks.index("0")
    assert result[0].M[zero_idx][x_idx] == -5
    assert any("Approximating strict inequality '<'" in message for message in caplog.messages)


def test_applyComparisonConstraint_literalGreaterVariableLogsWarning(caplog):
    # Arrange
    dmb = DMB(["x"])

    # Act
    with caplog.at_level("WARNING"):
        ImportanceFunctionBuilder._applyComparisonConstraint(dmb, Literal(5), VariableReference("x"), ">")

    # Assert
    x_idx = dmb.clocks.index("x")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[x_idx][zero_idx] == 5
    assert any("Approximating strict inequality '>'" in message for message in caplog.messages)


def test_applyComparisonConstraint_literalGreaterEqualVariableNoWarning(caplog):
    # Arrange
    dmb = DMB(["x"])

    # Act
    with caplog.at_level("WARNING"):
        ImportanceFunctionBuilder._applyComparisonConstraint(dmb, Literal(5), VariableReference("x"), ">=")

    # Assert
    x_idx = dmb.clocks.index("x")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[x_idx][zero_idx] == 5
    assert caplog.messages == []


def test_applyComparisonConstraint_variableGreaterLiteral():
    # Arrange
    dmb = DMB(["x"])

    # Act
    ImportanceFunctionBuilder._applyComparisonConstraint(dmb, VariableReference("x"), Literal(7), ">")

    # Assert
    x_idx = dmb.clocks.index("x")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[zero_idx][x_idx] == -7


def test_applyComparisonConstraint_unsupportedOperatorRaises():
    # Arrange
    dmb = DMB(["x"])

    # Act + Assert
    with pytest.raises(ValueError, match="Unsupported comparison operator"):
        ImportanceFunctionBuilder._applyComparisonConstraint(dmb, VariableReference("x"), Literal(1), "=")


def test_applyComparisonConstraint_unsupportedOperatorRaises_literalVariableBranch():
    # Arrange
    dmb = DMB(["x"])

    # Act + Assert
    with pytest.raises(ValueError, match="Unsupported comparison operator"):
        ImportanceFunctionBuilder._applyComparisonConstraint(dmb, Literal(1), VariableReference("x"), "=")


def test_applyConstraintExpressionToDMB_unknownBinaryOpRaises():
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression("+", VariableReference("x"), Literal(1))

    # Act + Assert
    with pytest.raises(ValueError, match="Unsupported guard operation"):
        ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])


def test_applyConstraintExpressionToDMB_orSplitsDmbs():
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression(
        "∨",
        BinaryExpression("<=", VariableReference("x"), Literal(10)),
        BinaryExpression(">=", VariableReference("x"), Literal(20))
    )

    # Act
    result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])

    # Assert
    assert len(result) == 2
    x_idx = result[0].clocks.index("x")
    zero_idx = result[0].clocks.index("0")
    upper_bounds = sorted([r.M[x_idx][zero_idx] for r in result])
    lower_bounds = sorted([r.M[zero_idx][x_idx] for r in result])
    assert upper_bounds == [10, math.inf]
    # Fresh DMBs enforce 0 - x <= 0 by default for non-negativity.
    assert lower_bounds == [-20, 0]


def test_applyConstraintExpressionToDMB_andAppliesBothConstraintsToSameDmb():
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression(
        "∧",
        BinaryExpression(">=", VariableReference("x"), Literal(5)),
        BinaryExpression("<=", VariableReference("x"), Literal(10))
    )

    # Act
    result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])

    # Assert
    assert len(result) == 1
    x_idx = result[0].clocks.index("x")
    zero_idx = result[0].clocks.index("0")
    assert result[0].M[zero_idx][x_idx] == -5
    assert result[0].M[x_idx][zero_idx] == 10


def test_applyConstraintExpressionToDMB_andWithOrBranchesCorrectly():
    # Arrange
    dmb = DMB(["x"])
    guard = BinaryExpression(
        "∧",
        BinaryExpression("<=", VariableReference("x"), Literal(10)),
        BinaryExpression(
            "∨",
            BinaryExpression(">=", VariableReference("x"), Literal(2)),
            BinaryExpression(">=", VariableReference("x"), Literal(7))
        )
    )

    # Act
    result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(guard, [dmb])

    # Assert
    assert len(result) == 2
    x_idx = result[0].clocks.index("x")
    zero_idx = result[0].clocks.index("0")
    assert all(r.M[x_idx][zero_idx] == 10 for r in result)
    assert sorted(r.M[zero_idx][x_idx] for r in result) == [-7, -2]


def test_applyConstraintExpressionToDMB_nonBinaryGuardReturnsSameReference():
    # Arrange
    dmbs = [DMB(["x"])]

    # Act
    result = ImportanceFunctionBuilder._applyConstraintExpressionToDMB(Literal(True), dmbs)

    # Assert
    assert result is dmbs


def test_mergeStateClasses_replacesDominatedOldState():
    # Arrange
    old_dmb = DMB(["x"])
    old_dmb.addConstraint("x", "0", 10)
    new_dmb = DMB(["x"])
    new_dmb.addConstraint("x", "0", 20)

    old_state = StateClass(locationName="A", dmb=old_dmb, distance=5)
    new_state = StateClass(locationName="A", dmb=new_dmb, distance=3)

    # Act
    merged = ImportanceFunctionBuilder._mergeStateClasses([old_state], [new_state])

    # Assert
    assert len(merged) == 1
    assert merged[0] is new_state


def test_mergeStateClasses_skipsDominatedNewState():
    # Arrange
    old_dmb = DMB(["x"])
    old_dmb.addConstraint("x", "0", 20)
    new_dmb = DMB(["x"])
    new_dmb.addConstraint("x", "0", 10)

    old_state = StateClass(locationName="A", dmb=old_dmb, distance=3)
    new_state = StateClass(locationName="A", dmb=new_dmb, distance=5)

    # Act
    merged = ImportanceFunctionBuilder._mergeStateClasses([old_state], [new_state])

    # Assert
    assert len(merged) == 1
    assert merged[0] is old_state


def test_mergeStateClasses_keepsBothWhenNeitherDominates():
    # Arrange
    old_dmb = DMB(["x"])
    old_dmb.addConstraint("x", "0", 10)
    new_dmb = DMB(["x"])
    new_dmb.addConstraint("0", "x", -3)

    old_state = StateClass(locationName="A", dmb=old_dmb, distance=3)
    new_state = StateClass(locationName="A", dmb=new_dmb, distance=3)

    # Act
    merged = ImportanceFunctionBuilder._mergeStateClasses([old_state], [new_state])

    # Assert
    assert len(merged) == 2
    assert old_state in merged
    assert new_state in merged


def test_mergeStateClasses_raisesWhenIncomingDmbIsNone():
    # Arrange
    old_state = StateClass(locationName="A", dmb=DMB(["x"]), distance=1)
    incoming_state = StateClass(locationName="A", dmb=None, distance=2)

    # Act + Assert
    with pytest.raises(ValueError, match="DMB should not be None"):
        ImportanceFunctionBuilder._mergeStateClasses([old_state], [incoming_state])


def test_mergeStateClasses_raisesWhenExistingDmbIsNone():
    # Arrange
    old_state = StateClass(locationName="A", dmb=None, distance=1)
    incoming_state = StateClass(locationName="A", dmb=DMB(["x"]), distance=2)

    # Act + Assert
    with pytest.raises(ValueError, match="DMB should not be None"):
        ImportanceFunctionBuilder._mergeStateClasses([old_state], [incoming_state])


def test_applyClockResets_removesOnlyMatchingDestinationAndClock():
    # Arrange
    src = Location(name="A", timeProgress=Literal(value=True))
    target = Location(name="target", timeProgress=Literal(value=True))
    other = Location(name="B", timeProgress=Literal(value=True))

    dmb = DMB(["x", "y"])
    dmb.addConstraint("x", "0", 9)
    dmb.addConstraint("y", "0", 4)

    edge = Edge(
        location=src,
        guard=Literal(value=True),
        destinations=[
            Destination(
                location=target,
                assignments=[
                    Assignment(ref="x", value=Literal(0)),
                    Assignment(ref="z", value=Literal(0)),
                    Assignment(ref="y", value=Distribution(type="uniform", args=[])),
                ],
            ),
            Destination(
                location=other,
                assignments=[Assignment(ref="y", value=Literal(0))],
            ),
        ],
    )
    current = StateClass(locationName="target", dmb=dmb, distance=0)

    # Act
    ImportanceFunctionBuilder._applyClockResets(dmb, edge, current)

    # Assert
    x_idx = dmb.clocks.index("x")
    y_idx = dmb.clocks.index("y")
    zero_idx = dmb.clocks.index("0")
    assert dmb.M[x_idx][zero_idx] == math.inf
    assert dmb.M[y_idx][zero_idx] == 4


def test_timeDistanceDictBuilder_returnsTargetIfNoIncomingEdges():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="onlyTarget",
        locations=[target],
        initial_locations=[target],
        variables=[Variable(name="x", type="clock")],
        edges=[],
    )

    # Act
    result = ImportanceFunctionBuilder._timeDistanceDictBuilder(automaton)

    # Assert
    assert "target" in result
    assert len(result["target"]) == 1
    assert result["target"][0].distance == 0
    assert result["target"][0].dmb is not None


def test_timeDistanceDictBuilder_raisesWhenTargetLocationMissing():
    # Arrange
    start = Location(name="A", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="missingTarget",
        locations=[start],
        initial_locations=[start],
        variables=[],
        edges=[],
    )

    # Act + Assert
    with pytest.raises(ValueError, match="Location target not found"):
        ImportanceFunctionBuilder._timeDistanceDictBuilder(automaton)


def test_timeDistanceDictBuilder_buildsPredecessorClassWithConstraintAndReset():
    # Arrange
    loc_a = Location(name="A", timeProgress=BinaryExpression("<=", VariableReference("x"), Literal(100)))
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="predecessor",
        locations=[loc_a, target],
        initial_locations=[loc_a],
        variables=[Variable(name="x", type="clock")],
        edges=[
            Edge(
                location=loc_a,
                guard=BinaryExpression("<=", VariableReference("x"), Literal(7)),
                destinations=[Destination(location=target, assignments=[Assignment(ref="x", value=Literal(0))])],
            )
        ],
    )

    # Act
    result = ImportanceFunctionBuilder._timeDistanceDictBuilder(automaton)

    # Assert
    assert "A" in result
    predecessor = result["A"][0]
    assert predecessor.distance == 1
    assert predecessor.dmb is not None
    x_idx = predecessor.dmb.clocks.index("x")
    zero_idx = predecessor.dmb.clocks.index("0")
    assert predecessor.dmb.M[x_idx][zero_idx] == 7


def test_timeDistanceDictBuilder_raisesWhenDeepcopyReturnsNone(monkeypatch):
    # Arrange
    loc_a = Location(name="A", timeProgress=Literal(value=True))
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="deepcopyNone",
        locations=[loc_a, target],
        initial_locations=[loc_a],
        variables=[],
        edges=[
            Edge(
                location=loc_a,
                guard=Literal(value=True),
                destinations=[Destination(location=target, assignments=[])],
            )
        ],
    )

    def fake_deepcopy(_):
        return None

    monkeypatch.setattr("importanceFunctionBuilder.copy.deepcopy", fake_deepcopy)

    # Act + Assert
    with pytest.raises(ValueError, match="DMB should not be None"):
        ImportanceFunctionBuilder._timeDistanceDictBuilder(automaton)


def test_timeDistanceDictBuilder_mergesWhenSourceAlreadyVisited():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="selfLoopTarget",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[
            Edge(
                location=target,
                guard=Literal(value=True),
                destinations=[Destination(location=target, assignments=[])],
            )
        ],
    )

    # Act
    result = ImportanceFunctionBuilder._timeDistanceDictBuilder(automaton)

    # Assert
    assert "target" in result
    assert len(result["target"]) >= 1


def test_importanceFunction_returnsTimeDistanceWhenSatisfied():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="forImportance",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[],
    )
    builder = ImportanceFunctionBuilder(automaton)

    dmb = DMB(["x"])
    dmb.addConstraint("x", "0", 10)
    builder.timeDistanceDict = {"A": [StateClass("A", dmb, 4)]}
    builder.hopDistanceDict = {"A": 99}
    snapshot = StateSnapShot(stateName="A", clocks=[Clock(name="x", value=3)])

    # Act
    result = builder.importanceFunction(snapshot)

    # Assert
    assert result == 4


def test_importanceFunction_returnsLargeDistanceWhenNoTimeClassSatisfied():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="forImportanceFallback",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[],
    )
    builder = ImportanceFunctionBuilder(automaton)

    dmb = DMB(["x"])
    dmb.addConstraint("x", "0", 1)
    builder.timeDistanceDict = {"A": [StateClass("A", dmb, 2), StateClass("A", None, 1)]}
    builder.hopDistanceDict = {"A": 7}
    snapshot = StateSnapShot(stateName="A", clocks=[Clock(name="x", value=5)])

    # Act
    result = builder.importanceFunction(snapshot)

    # Assert
    assert result == LARGE_DISTANCE


def test_importanceFunction_fallsBackToHopDistanceWhenNoTimeClassesForLocation():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="forImportanceNoLocation",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[],
    )
    builder = ImportanceFunctionBuilder(automaton)

    builder.timeDistanceDict = {}
    builder.hopDistanceDict = {"A": 11}
    snapshot = StateSnapShot(stateName="A", clocks=[])

    # Act
    result = builder.importanceFunction(snapshot)

    # Assert
    assert result == 11


def test_build_returnsImportanceFunctionCallable():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="build",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[],
    )
    builder = ImportanceFunctionBuilder(automaton)

    # Act
    fn = builder.build()

    # Assert
    assert callable(fn)
    assert fn == builder.importanceFunction


def test_constructor_initializesDistanceDictionaries():
    # Arrange
    target = Location(name="target", timeProgress=Literal(value=True))
    automaton = Automaton(
        name="ctor",
        locations=[target],
        initial_locations=[target],
        variables=[],
        edges=[],
    )

    # Act
    builder = ImportanceFunctionBuilder(automaton)

    # Assert
    assert builder.automaton is automaton
    assert builder.hopDistanceDict["target"] == 0
    assert "target" in builder.timeDistanceDict

# endregion
