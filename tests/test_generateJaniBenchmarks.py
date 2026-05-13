from __future__ import annotations

import math

import generateJaniBenchmarks as gen


def test_parseCliArgs_exposes_new_safety_flags():
    args = gen.parseCliArgs(
        [
            "--num_states",
            "7",
            "--num_clocks",
            "1",
            "--branching_factor",
            "1.5",
            "--max_time_bound",
            "10",
            "--rare_event_probability",
            "0.05",
            "--seed",
            "1",
        ]
    )

    assert args.min_transition_prob == gen.DEFAULT_MIN_TRANSITION_PROB
    assert args.escape_prob == gen.DEFAULT_ESCAPE_PROB


def test_buildBenchmarkModel_generates_positive_probabilities_and_valid_structure():
    params = gen.GenerationParams(
        numStates=7,
        numClocks=1,
        branchingFactor=1.5,
        maxTimeBound=10.0,
        rareEventProbability=0.05,
        seed=1,
    )

    model = gen.buildBenchmarkModel(params, "test-sta", 0)
    automaton = model["automata"][0]

    assert model["type"] == "sta"
    assert model["name"] == "test-sta-n7-c1-b1p5-t10-r0p05-s1-i000"
    assert len(automaton["locations"]) == params.numStates

    location_names = {location["name"] for location in automaton["locations"]}
    assert gen.FAILURE_LOCATION_NAME in location_names
    assert f"loc_{params.numStates - 1}" in location_names

    for edge in automaton["edges"]:
        probabilities = [float(destination["probability"]["exp"]) for destination in edge["destinations"]]
        assert probabilities
        assert all(probability > 0.0 for probability in probabilities)
        assert math.isclose(sum(probabilities), 1.0, rel_tol=1e-9, abs_tol=1e-9)


def test_determinism_check_is_stable_for_valid_parameters():
    params = gen.GenerationParams(
        numStates=7,
        numClocks=1,
        branchingFactor=1.5,
        maxTimeBound=10.0,
        rareEventProbability=0.05,
        seed=2,
    )

    gen.runDeterminismCheck(params, "test-sta", 1)
