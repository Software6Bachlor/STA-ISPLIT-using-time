import pytest

from importanceFunctionBuilder import ImportanceFunctionBuilder
from models.STA import (
    Assignment,
    Automaton,
    BinaryExpression,
    Destination,
    Distribution,
    Edge,
    Literal,
    Location,
    Variable,
    VariableReference,
)
from models.clock import Clock
from models.stateSnapshot import StateSnapShot


LARGE_DISTANCE = int(1e9)


def test_importanceFunctionBuilder_fullFlow_endToEnd():
    # Automaton shape (forward): Start -> Mid -> target
    # This exercises constructor, build(), time-distance matching, and hop-distance fallback.
    target = Location(name="target", timeProgress=Literal(value=True))
    mid = Location(name="Mid", timeProgress=BinaryExpression("<=", VariableReference("x"), Literal(10)))
    start = Location(name="Start", timeProgress=BinaryExpression("<=", VariableReference("x"), Literal(20)))

    automaton = Automaton(
        name="fullFlow",
        locations=[target, mid, start],
        initial_locations=[start.name],
        variables=[Variable(name="x", type="clock")],
        edges=[
            Edge(
                location=start.name,
                guard=BinaryExpression("<=", VariableReference("x"), Literal(5)),
                destinations=[Destination(location=mid.name, assignments=[])],
            ),
            Edge(
                location=mid.name,
                guard=BinaryExpression("<=", VariableReference("x"), Literal(3)),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
        ],
    )

    builder = ImportanceFunctionBuilder(automaton, target)
    importance = builder.build()

    # For Mid with x <= 3, time-distance class applies directly (distance 1 to target).
    mid_time_snapshot = StateSnapShot(locationName="Mid", clocks=[Clock(name="x", value=2)])
    assert importance(mid_time_snapshot) == 1

    # For Mid with x > 3, a time-distance class exists but does not apply,
    # so we return a large penalty distance.
    mid_hop_snapshot = StateSnapShot(locationName="Mid", clocks=[Clock(name="x", value=7)])
    assert importance(mid_hop_snapshot) == LARGE_DISTANCE

    # Start has no computed time-distance class in current implementation, so hop distance is used.
    start_snapshot = StateSnapShot(locationName="Start", clocks=[Clock(name="x", value=1)])
    assert importance(start_snapshot) == 2


def test_importanceFunctionBuilder_bigAutomaton_13States_edgeCases():
    # 13 locations total: target + S1..S12
    target = Location(name="target", timeProgress=Literal(value=True))
    s1 = Location(name="S1", timeProgress=Literal(value=True))
    s2 = Location(name="S2", timeProgress=Literal(value=True))
    s3 = Location(name="S3", timeProgress=Literal(value=True))
    s4 = Location(name="S4", timeProgress=Literal(value=True))
    s5 = Location(name="S5", timeProgress=Literal(value=True))
    s6 = Location(name="S6", timeProgress=Literal(value=True))
    s7 = Location(name="S7", timeProgress=Literal(value=True))
    s8 = Location(name="S8", timeProgress=Literal(value=True))
    s9 = Location(name="S9", timeProgress=Literal(value=True))
    s10 = Location(name="S10", timeProgress=Literal(value=True))
    s11 = Location(name="S11", timeProgress=Literal(value=True))
    s12 = Location(name="S12", timeProgress=Literal(value=True))

    automaton = Automaton(
        name="bigFlow",
        # target first so hop-distance is measured backward from rare event
        locations=[target, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12],
        initial_locations=[s11.name],
        variables=[Variable(name="x", type="clock"), Variable(name="y", type="clock")],
        edges=[
            # Direct predecessors to target with varied guard forms.
            Edge(
                location=s1.name,
                guard=BinaryExpression("<=", VariableReference("x"), Literal(5)),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            Edge(
                location=s2.name,
                guard=BinaryExpression(">=", VariableReference("x"), Literal(3)),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            Edge(
                location=s3.name,
                guard=BinaryExpression("<=", Literal(2), VariableReference("x")),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            Edge(
                location=s4.name,
                guard=BinaryExpression(">", Literal(8), VariableReference("x")),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            Edge(
                location=s5.name,
                guard=BinaryExpression(
                    "∧",
                    BinaryExpression("<=", VariableReference("x"), Literal(4)),
                    BinaryExpression(">=", VariableReference("y"), Literal(1)),
                ),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            Edge(
                location=s6.name,
                guard=BinaryExpression(
                    "∨",
                    BinaryExpression("<=", VariableReference("x"), Literal(2)),
                    BinaryExpression(">=", VariableReference("x"), Literal(9)),
                ),
                destinations=[Destination(location=target.name, assignments=[])],
            ),
            # Reset/multi-destination case.
            Edge(
                location=s7.name,
                guard=BinaryExpression("<=", VariableReference("x"), Literal(6)),
                destinations=[
                    Destination(
                        location=target.name,
                        assignments=[
                            Assignment(ref="x", value=Literal(0)),
                            Assignment(ref="y", value=Distribution(type="uniform", args=[])),
                        ],
                    ),
                    Destination(
                        location=s8.name,
                        assignments=[Assignment(ref="y", value=Literal(0))],
                    ),
                ],
            ),
            # Multi-hop predecessors (fallback via hop distance in current algorithm).
            Edge(
                location=s8.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s6.name, assignments=[])],
            ),
            Edge(
                location=s9.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s1.name, assignments=[])],
            ),
            Edge(
                location=s10.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s5.name, assignments=[])],
            ),
            Edge(
                location=s11.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s9.name, assignments=[])],
            ),
            # Cycle and unreachable component.
            Edge(
                location=s10.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s11.name, assignments=[])],
            ),
            Edge(
                location=s12.name,
                guard=Literal(value=True),
                destinations=[Destination(location=s12.name, assignments=[])],
            ),
        ],
    )

    builder = ImportanceFunctionBuilder(automaton, target)
    importance = builder.build()

    # Guard-based time classes for direct predecessors.
    assert importance(StateSnapShot(locationName="S1", clocks=[Clock("x", 5), Clock("y", 0)])) == 1
    assert importance(StateSnapShot(locationName="S2", clocks=[Clock("x", 4), Clock("y", 0)])) == 1
    assert importance(StateSnapShot(locationName="S3", clocks=[Clock("x", 2), Clock("y", 0)])) == 1
    assert importance(StateSnapShot(locationName="S4", clocks=[Clock("x", 5), Clock("y", 0)])) == 1
    assert importance(StateSnapShot(locationName="S5", clocks=[Clock("x", 4), Clock("y", 1)])) == 1
    assert importance(StateSnapShot(locationName="S6", clocks=[Clock("x", 10), Clock("y", 0)])) == 1

    # Unsatisfied time guard for a direct predecessor returns large penalty distance.
    assert importance(StateSnapShot(locationName="S1", clocks=[Clock("x", 8), Clock("y", 0)])) == LARGE_DISTANCE

    # Multi-hop predecessors may now also receive propagated time-distance classes.
    assert importance(StateSnapShot(locationName="S8", clocks=[Clock("x", 0), Clock("y", 0)])) == 2
    assert importance(StateSnapShot(locationName="S9", clocks=[Clock("x", 0), Clock("y", 0)])) == 2
    assert importance(StateSnapShot(locationName="S10", clocks=[Clock("x", 0), Clock("y", 0)])) == 2
    assert importance(StateSnapShot(locationName="S11", clocks=[Clock("x", 0), Clock("y", 0)])) == 3

    # Unreachable from target should not have hop distance and therefore raises.
    with pytest.raises(KeyError):
        importance(StateSnapShot(locationName="S12", clocks=[Clock("x", 0), Clock("y", 0)]))
