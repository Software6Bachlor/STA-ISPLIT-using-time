from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

DEFAULT_OUTPUT_DIR = Path("models/benchmark/jani")
DEFAULT_MODEL_PREFIX = "generated-sta"

DEFAULT_MIN_TRANSITION_PROB = 1e-12
DEFAULT_ESCAPE_PROB = 0.0

TIME_BOUND_CONSTANT_NAME = "TIME_BOUND"
FAILURE_VARIABLE_NAME = "failure"
RISK_VARIABLE_NAME = "risk_level"

FAILURE_LOCATION_NAME = "loc_0"
SAFE_SINK_LABEL = "safe_sink"
AUTOMATON_NAME = "MonolithicSTA"

RISK_MAX = 3

OP_AND = "\u2227"
OP_OR = "\u2228"
OP_NOT = "\u00ac"
OP_GE = "\u2265"
OP_LE = "\u2264"


@dataclass(frozen=True, slots=True)
class GenerationParams:
    numStates: int
    numClocks: int
    branchingFactor: float
    maxTimeBound: float
    rareEventProbability: float
    seed: int


@dataclass(frozen=True, slots=True)
class KeyLocations:
    failure: str
    safeSink: str
    initial: str
    pathA: str
    gatewayA: str
    pathB: str
    gatewayB: str


def parseCliArgs(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate monolithic stochastic timed automata benchmarks in JANI JSON format "
            "for the Modest Toolset."
        )
    )
    parser.add_argument("--num_states", required=True, help="int, list (a,b), or range (start:end[:step])")
    parser.add_argument("--num_clocks", required=True, help="int, list (a,b), or range (start:end[:step])")
    parser.add_argument("--branching_factor", required=True, help="float/int, list, or range")
    parser.add_argument("--max_time_bound", required=True, help="float/int, list, or range")
    parser.add_argument("--rare_event_probability", required=True, help="float in (0,1), list, or range")
    parser.add_argument("--seed", required=True, help="int, list, or range")
    parser.add_argument("--output_dir", default=str(DEFAULT_OUTPUT_DIR), help="Destination directory for .jani files")
    parser.add_argument("--model_prefix", default=DEFAULT_MODEL_PREFIX, help="Prefix for model/file names")
    parser.add_argument("--dry_run", action="store_true", help="Build and validate models without writing files")
    parser.add_argument(
        "--determinism_check",
        action="store_true",
        help="Regenerate each model and compare canonical JSON to verify deterministic generation",
    )
    parser.add_argument(
        "--min_transition_prob",
        type=float,
        default=DEFAULT_MIN_TRANSITION_PROB,
        help="Minimum allowed transition probability (small positive epsilon)",
    )
    parser.add_argument(
        "--escape_prob",
        type=float,
        default=DEFAULT_ESCAPE_PROB,
        help="If >0, add a fallback tiny-probability transition to the safe sink when needed",
    )
    return parser.parse_args(args)


def parseSweepValues(rawValue: str, caster: Callable[[str], int | float], parameterName: str) -> list[int | float]:
    parts = [part.strip() for part in rawValue.split(",") if part.strip()]
    if not parts:
        raise ValueError(f"Parameter '{parameterName}' must contain at least one value.")

    values: list[int | float] = []
    for part in parts:
        if ":" in part:
            values.extend(parseRangeValues(part, caster, parameterName))
        else:
            values.append(castSingleValue(part, caster, parameterName))

    return dedupeValues(values)


def parseRangeValues(rawRange: str, caster: Callable[[str], int | float], parameterName: str) -> list[int | float]:
    bits = [bit.strip() for bit in rawRange.split(":")]
    if len(bits) not in (2, 3):
        raise ValueError(
            f"Range for '{parameterName}' must be 'start:end' or 'start:end:step'. Got '{rawRange}'."
        )

    start = castSingleValue(bits[0], caster, parameterName)
    end = castSingleValue(bits[1], caster, parameterName)
    if len(bits) == 3:
        step = castSingleValue(bits[2], caster, parameterName)
    else:
        step = 1 if end >= start else -1

    if step == 0:
        raise ValueError(f"Range step for '{parameterName}' cannot be 0.")

    direction = end - start
    if direction > 0 and step < 0:
        raise ValueError(f"Range step for '{parameterName}' moves away from end value.")
    if direction < 0 and step > 0:
        raise ValueError(f"Range step for '{parameterName}' moves away from end value.")

    isIntRange = caster is int
    values: list[int | float] = []

    if isIntRange:
        current = int(start)
        final = int(end)
        delta = int(step)
        if delta > 0:
            while current <= final:
                values.append(current)
                current += delta
        else:
            while current >= final:
                values.append(current)
                current += delta
        return values

    current = float(start)
    final = float(end)
    delta = float(step)
    tolerance = 1e-12

    if delta > 0:
        while current <= final + tolerance:
            values.append(round(current, 12))
            current += delta
    else:
        while current >= final - tolerance:
            values.append(round(current, 12))
            current += delta

    return values


def castSingleValue(rawValue: str, caster: Callable[[str], int | float], parameterName: str) -> int | float:
    try:
        value = caster(rawValue)
    except ValueError as error:
        raise ValueError(f"Invalid value '{rawValue}' for parameter '{parameterName}'.") from error
    return value


def dedupeValues(values: list[int | float]) -> list[int | float]:
    deduped: list[int | float] = []
    seen: set[int | float | str] = set()

    for value in values:
        marker: int | float | str
        if isinstance(value, float):
            marker = f"{value:.12f}"
        else:
            marker = value

        if marker not in seen:
            seen.add(marker)
            deduped.append(value)

    return deduped


def buildParameterGrid(cliArgs: argparse.Namespace) -> list[GenerationParams]:
    numStatesValues = [int(value) for value in parseSweepValues(cliArgs.num_states, int, "num_states")]
    numClocksValues = [int(value) for value in parseSweepValues(cliArgs.num_clocks, int, "num_clocks")]
    branchingFactorValues = [
        float(value) for value in parseSweepValues(cliArgs.branching_factor, float, "branching_factor")
    ]
    maxTimeBoundValues = [
        float(value) for value in parseSweepValues(cliArgs.max_time_bound, float, "max_time_bound")
    ]
    rareEventProbabilityValues = [
        float(value)
        for value in parseSweepValues(cliArgs.rare_event_probability, float, "rare_event_probability")
    ]
    seedValues = [int(value) for value in parseSweepValues(cliArgs.seed, int, "seed")]

    allParams: list[GenerationParams] = []

    for combination in itertools.product(
        numStatesValues,
        numClocksValues,
        branchingFactorValues,
        maxTimeBoundValues,
        rareEventProbabilityValues,
        seedValues,
    ):
        params = GenerationParams(
            numStates=combination[0],
            numClocks=combination[1],
            branchingFactor=combination[2],
            maxTimeBound=combination[3],
            rareEventProbability=combination[4],
            seed=combination[5],
        )
        validateGenerationParams(params)
        allParams.append(params)

    return allParams


def validateGenerationParams(params: GenerationParams) -> None:
    if params.numStates < 7:
        raise ValueError("num_states must be at least 7 to guarantee multiple alternative failure paths and a safe sink.")

    if params.numClocks < 1:
        raise ValueError("num_clocks must be at least 1.")

    activeStateCount = params.numStates - 2
    if params.numClocks > activeStateCount:
        raise ValueError(
            "num_clocks must be less than or equal to num_states - 2 so each clock is used in guards, invariants, and resets."
        )

    if params.branchingFactor < 1:
        raise ValueError("branching_factor must be >= 1.")

    if params.maxTimeBound <= 1:
        raise ValueError("max_time_bound must be > 1.")

    if not (0 < params.rareEventProbability < 1):
        raise ValueError("rare_event_probability must be strictly between 0 and 1.")


def buildBenchmarkModel(
    params: GenerationParams,
    modelPrefix: str,
    modelIndex: int,
    min_transition_prob: float = DEFAULT_MIN_TRANSITION_PROB,
    escape_prob: float = DEFAULT_ESCAPE_PROB,
) -> dict:
    rng = random.Random(params.seed)

    locationNames = [f"loc_{index}" for index in range(params.numStates)]
    keyLocations = buildKeyLocations(params)
    activeLocations = [
        locationName
        for locationName in locationNames
        if locationName not in {keyLocations.failure, keyLocations.safeSink}
    ]

    clockNames = [f"c_{clockIndex}" for clockIndex in range(params.numClocks)]
    delayNames = [f"x_{clockIndex}" for clockIndex in range(params.numClocks)]
    clockByLocation = assignClocksToLocations(activeLocations, params.numClocks)

    adjacencyMap = buildAdjacencyMap(activeLocations, keyLocations, params, rng)

    locations = buildLocations(locationNames, keyLocations, clockByLocation, clockNames, delayNames, params, rng)
    edges = buildEdges(adjacencyMap, keyLocations, clockByLocation, clockNames, delayNames, params, rng)

    modelName = buildModelName(modelPrefix, params, modelIndex)

    modelData = {
        "jani-version": 1,
        "name": modelName,
        "type": "sta",
        "features": ["derived-operators"],
        "constants": [
            {
                "name": TIME_BOUND_CONSTANT_NAME,
                "type": "real",
                "value": round(params.maxTimeBound, 6),
            }
        ],
        "variables": [
            {
                "name": FAILURE_VARIABLE_NAME,
                "type": "bool",
                "initial-value": False,
            },
            {
                "name": RISK_VARIABLE_NAME,
                "type": {
                    "kind": "bounded",
                    "base": "int",
                    "lower-bound": 0,
                    "upper-bound": RISK_MAX,
                },
                "initial-value": 0,
            },
        ],
        "properties": [
            {
                "name": "P_Failure",
                "expression": {
                    "op": "filter",
                    "fun": "max",
                    "values": {
                        "op": "Pmax",
                        "exp": {
                            "op": "F",
                            "exp": FAILURE_VARIABLE_NAME,
                            "time-bounds": {
                                "upper": TIME_BOUND_CONSTANT_NAME,
                            },
                        },
                    },
                    "states": {
                        "op": "initial",
                    },
                },
            }
        ],
        "automata": [
            {
                "name": AUTOMATON_NAME,
                "locations": locations,
                "initial-locations": [keyLocations.initial],
                "variables": buildAutomatonVariables(clockNames, delayNames, params, rng),
                "edges": edges,
            }
        ],
        "system": {
            "elements": [
                {
                    "automaton": AUTOMATON_NAME,
                }
            ]
        },
    }

    enforce_min_transition_prob_on_model(modelData, keyLocations, min_transition_prob, escape_prob)
    runSamplingFeasibilityCheck(modelData, params, keyLocations)
    validateModelStructure(modelData, params, keyLocations, clockNames)
    return modelData


def buildKeyLocations(params: GenerationParams) -> KeyLocations:
    return KeyLocations(
        failure=FAILURE_LOCATION_NAME,
        safeSink=f"loc_{params.numStates - 1}",
        initial="loc_1",
        pathA="loc_2",
        gatewayA="loc_3",
        pathB="loc_4",
        gatewayB="loc_5",
    )


def buildModelName(modelPrefix: str, params: GenerationParams, modelIndex: int) -> str:
    branchingToken = sanitizeToken(params.branchingFactor)
    timeToken = sanitizeToken(params.maxTimeBound)
    rareToken = sanitizeToken(params.rareEventProbability)

    return (
        f"{modelPrefix}"
        f"-n{params.numStates}"
        f"-c{params.numClocks}"
        f"-b{branchingToken}"
        f"-t{timeToken}"
        f"-r{rareToken}"
        f"-s{params.seed}"
        f"-i{modelIndex:03d}"
    )


def sanitizeToken(value: float) -> str:
    text = f"{value:.6g}"
    return text.replace("-", "m").replace(".", "p")


def assignClocksToLocations(activeLocations: list[str], numClocks: int) -> dict[str, int]:
    clockByLocation: dict[str, int] = {}
    for locationIndex, locationName in enumerate(activeLocations):
        clockByLocation[locationName] = locationIndex % numClocks
    return clockByLocation


def buildAdjacencyMap(
    activeLocations: list[str],
    keyLocations: KeyLocations,
    params: GenerationParams,
    rng: random.Random,
) -> dict[str, set[str]]:
    adjacencyMap = {locationName: set() for locationName in activeLocations}

    extraCore = [
        locationName
        for locationName in activeLocations
        if locationName
        not in {
            keyLocations.initial,
            keyLocations.pathA,
            keyLocations.gatewayA,
            keyLocations.pathB,
            keyLocations.gatewayB,
        }
    ]

    # Guaranteed alternative paths toward failure gateways.
    adjacencyMap[keyLocations.initial].update({keyLocations.pathA, keyLocations.pathB})
    adjacencyMap[keyLocations.pathA].add(keyLocations.gatewayA)
    adjacencyMap[keyLocations.pathB].add(keyLocations.gatewayB)

    recoveryTargets = [keyLocations.initial] + extraCore
    if not recoveryTargets:
        recoveryTargets = [keyLocations.initial]

    adjacencyMap[keyLocations.gatewayA].add(rng.choice(recoveryTargets))
    adjacencyMap[keyLocations.gatewayB].add(rng.choice(recoveryTargets))

    # Build irregular core cycles and merges.
    if extraCore:
        adjacencyMap[keyLocations.initial].add(extraCore[0])
        for index, source in enumerate(extraCore):
            nextNode = extraCore[(index + 1) % len(extraCore)]
            adjacencyMap[source].add(nextNode)
            if index > 0:
                adjacencyMap[source].add(extraCore[index - 1])
            adjacencyMap[source].add(
                rng.choice(
                    [
                        keyLocations.initial,
                        keyLocations.pathA,
                        keyLocations.pathB,
                        keyLocations.gatewayA,
                        keyLocations.gatewayB,
                    ]
                )
            )

    mergeHubCount = min(2, len(activeLocations))
    mergeHubs = rng.sample(activeLocations, k=mergeHubCount)

    candidateTargetsBySource: dict[str, list[str]] = {}
    for source in activeLocations:
        candidateTargetsBySource[source] = [
            locationName
            for locationName in activeLocations
            if locationName != source
        ] + [keyLocations.safeSink]

    for source in activeLocations:
        desiredOut = max(1, int(round(params.branchingFactor + rng.uniform(-0.75, 0.75))))
        if source in {keyLocations.initial, keyLocations.gatewayA, keyLocations.gatewayB}:
            desiredOut = max(desiredOut, 2)

        while len(adjacencyMap[source]) < desiredOut:
            target = weightedDestinationChoice(source, candidateTargetsBySource[source], keyLocations, rng)
            adjacencyMap[source].add(target)

        if rng.random() < 0.35:
            adjacencyMap[source].add(source)

        backwardCandidates = [
            locationName
            for locationName in activeLocations
            if locationSortKey(locationName) < locationSortKey(source)
        ]
        if backwardCandidates and rng.random() < 0.5:
            adjacencyMap[source].add(rng.choice(backwardCandidates))

        if source not in mergeHubs and rng.random() < 0.45:
            adjacencyMap[source].add(rng.choice(mergeHubs))

    # Explicit recovery edges from risky states.
    for riskyState in [keyLocations.pathA, keyLocations.pathB, keyLocations.gatewayA, keyLocations.gatewayB]:
        adjacencyMap[riskyState].add(rng.choice(recoveryTargets))

    # Ensure safe sink is reachable from several states.
    safeEntryCount = max(1, len(activeLocations) // 4)
    safeEntryStates = rng.sample(activeLocations, k=safeEntryCount)
    for source in safeEntryStates:
        adjacencyMap[source].add(keyLocations.safeSink)

    return adjacencyMap


def weightedDestinationChoice(
    source: str,
    candidates: list[str],
    keyLocations: KeyLocations,
    rng: random.Random,
) -> str:
    weightedCandidates: list[tuple[str, float]] = []

    for candidate in candidates:
        weight = 1.0

        if candidate == keyLocations.safeSink:
            weight *= 0.35
        if candidate in {keyLocations.gatewayA, keyLocations.gatewayB}:
            weight *= 1.8
        if candidate == keyLocations.initial:
            weight *= 1.5
        if locationSortKey(candidate) < locationSortKey(source):
            weight *= 1.3

        weightedCandidates.append((candidate, weight))

    totalWeight = sum(weight for _, weight in weightedCandidates)
    pick = rng.uniform(0.0, totalWeight)

    cumulative = 0.0
    for candidate, weight in weightedCandidates:
        cumulative += weight
        if pick <= cumulative:
            return candidate

    return weightedCandidates[-1][0]


def buildLocations(
    locationNames: list[str],
    keyLocations: KeyLocations,
    clockByLocation: dict[str, int],
    clockNames: list[str],
    delayNames: list[str],
    params: GenerationParams,
    rng: random.Random,
) -> list[dict]:
    locations: list[dict] = []

    for locationName in locationNames:
        locationData: dict = {"name": locationName}

        if locationName not in {keyLocations.failure, keyLocations.safeSink}:
            clockIndex = clockByLocation[locationName]
            clockName = clockNames[clockIndex]
            delayName = delayNames[clockIndex]
            locationData["time-progress"] = {
                "exp": buildInvariantExpression(locationName, clockName, delayName, params, rng)
            }

        locations.append(locationData)

    return locations


def buildInvariantExpression(
    locationName: str,
    clockName: str,
    delayName: str,
    params: GenerationParams,
    rng: random.Random,
) -> dict:
    locationIndex = locationSortKey(locationName)
    threshold = 1 + (locationIndex % RISK_MAX)
    maxLiteralBound = max(1.0, params.maxTimeBound)

    if (locationIndex + params.seed) % 2 == 0:
        return {
            "op": OP_LE,
            "left": clockName,
            "right": delayName,
        }

    hardLimit = round(maxLiteralBound * (0.35 + 0.5 * rng.random()), 6)
    hardLimit = max(1.0, min(hardLimit, maxLiteralBound))

    return {
        "op": OP_AND,
        "left": {
            "op": OP_OR,
            "left": {
                "op": "<",
                "left": RISK_VARIABLE_NAME,
                "right": threshold,
            },
            "right": {
                "op": OP_LE,
                "left": clockName,
                "right": delayName,
            },
        },
        "right": {
            "op": OP_OR,
            "left": {
                "op": OP_GE,
                "left": RISK_VARIABLE_NAME,
                "right": threshold,
            },
            "right": {
                "op": OP_LE,
                "left": clockName,
                "right": hardLimit,
            },
        },
    }


def buildEdges(
    adjacencyMap: dict[str, set[str]],
    keyLocations: KeyLocations,
    clockByLocation: dict[str, int],
    clockNames: list[str],
    delayNames: list[str],
    params: GenerationParams,
    rng: random.Random,
) -> list[dict]:
    edges: list[dict] = []

    for source in sorted(adjacencyMap.keys(), key=locationSortKey):
        destinationList = sorted(adjacencyMap[source], key=locationSortKey)
        destinationGroups = splitDestinationGroups(destinationList, rng)

        if source in {keyLocations.gatewayA, keyLocations.gatewayB}:
            ensureFailureDestination(destinationGroups, keyLocations.failure)

        clockIndex = clockByLocation[source]
        clockName = clockNames[clockIndex]
        delayName = delayNames[clockIndex]

        for groupIndex, destinationGroup in enumerate(destinationGroups):
            if not destinationGroup:
                continue

            guardExpression = buildGuardExpression(source, groupIndex, clockName, delayName, params, keyLocations)
            destinations = buildDestinations(
                source,
                destinationGroup,
                keyLocations,
                clockName,
                delayName,
                params,
                rng,
            )

            edges.append(
                {
                    "location": source,
                    "guard": {"exp": guardExpression},
                    "destinations": destinations,
                }
            )

    return edges


def splitDestinationGroups(destinationList: list[str], rng: random.Random) -> list[list[str]]:
    if len(destinationList) < 2:
        return [destinationList]

    shuffled = list(destinationList)
    rng.shuffle(shuffled)

    if rng.random() < 0.65:
        splitAt = max(1, len(shuffled) // 2)
        return [
            sorted(shuffled[:splitAt], key=locationSortKey),
            sorted(shuffled[splitAt:], key=locationSortKey),
        ]

    return [sorted(shuffled, key=locationSortKey)]


def ensureFailureDestination(destinationGroups: list[list[str]], failureLocation: str) -> None:
    if any(failureLocation in group for group in destinationGroups):
        return

    if not destinationGroups:
        destinationGroups.append([failureLocation])
        return

    destinationGroups[0].append(failureLocation)
    destinationGroups[0].sort(key=locationSortKey)


def buildGuardExpression(
    source: str,
    groupIndex: int,
    clockName: str,
    delayName: str,
    params: GenerationParams,
    keyLocations: KeyLocations,
) -> dict:
    baseGuard = {
        "op": OP_GE,
        "left": clockName,
        "right": delayName,
    }

    if source in {keyLocations.gatewayA, keyLocations.gatewayB}:
        tightBound = round(max(1.0, params.maxTimeBound * 0.35), 6)
        return {
            "op": OP_AND,
            "left": baseGuard,
            "right": {
                "op": OP_LE,
                "left": delayName,
                "right": tightBound,
            },
        }

    if groupIndex == 0:
        return baseGuard

    threshold = 1 + (locationSortKey(source) % RISK_MAX)
    if groupIndex % 2 == 1:
        riskConstraint = {
            "op": OP_LE,
            "left": RISK_VARIABLE_NAME,
            "right": threshold,
        }
    else:
        riskConstraint = {
            "op": OP_GE,
            "left": RISK_VARIABLE_NAME,
            "right": threshold,
        }

    return {
        "op": OP_AND,
        "left": baseGuard,
        "right": riskConstraint,
    }


def buildDestinations(
    source: str,
    destinationGroup: list[str],
    keyLocations: KeyLocations,
    clockName: str,
    delayName: str,
    params: GenerationParams,
    rng: random.Random,
) -> list[dict]:
    probabilities = buildProbabilityMap(source, destinationGroup, keyLocations, params, rng)

    destinations: list[dict] = []
    for destination in destinationGroup:
        destinationData = {
            "location": destination,
            "probability": {
                "exp": probabilities[destination],
            },
            "assignments": buildAssignments(
                source,
                destination,
                keyLocations,
                clockName,
                delayName,
                params,
                rng,
            ),
        }
        destinations.append(destinationData)

    return destinations


def buildProbabilityMap(
    source: str,
    destinationGroup: list[str],
    keyLocations: KeyLocations,
    params: GenerationParams,
    rng: random.Random,
) -> dict[str, float]:
    if len(destinationGroup) == 1:
        return {destinationGroup[0]: 1.0}

    if source in {keyLocations.gatewayA, keyLocations.gatewayB} and keyLocations.failure in destinationGroup:
        return buildGatewayProbabilityMap(destinationGroup, keyLocations, params, rng)

    weights: dict[str, float] = {}
    for destination in destinationGroup:
        weight = rng.uniform(0.5, 2.5)
        if destination == keyLocations.safeSink:
            weight *= 0.4
        if destination == source:
            weight *= 1.2
        weights[destination] = weight

    return normalizeWeights(weights)


def buildGatewayProbabilityMap(
    destinationGroup: list[str],
    keyLocations: KeyLocations,
    params: GenerationParams,
    rng: random.Random,
) -> dict[str, float]:
    destinations = list(destinationGroup)
    if keyLocations.failure not in destinations:
        raise ValueError("Gateway destination group must contain the failure location.")

    nonFailureDestinations = [destination for destination in destinations if destination != keyLocations.failure]
    if not nonFailureDestinations:
        nonFailureDestinations = [keyLocations.initial]
        destinations.append(keyLocations.initial)

    rareProbability = min(max(params.rareEventProbability, 1e-10), 1 - 1e-10)

    nonFailureWeights = {
        destination: rng.uniform(0.5, 2.0)
        for destination in nonFailureDestinations
    }
    normalizedNonFailure = normalizeWeights(nonFailureWeights)

    probabilities = {keyLocations.failure: rareProbability}
    remaining = 1.0 - rareProbability

    assigned = 0.0
    sortedNonFailure = sorted(nonFailureDestinations, key=locationSortKey)
    for index, destination in enumerate(sortedNonFailure):
        if index == len(sortedNonFailure) - 1:
            probability = round(remaining - assigned, 12)
        else:
            probability = round(remaining * normalizedNonFailure[destination], 12)
            assigned += probability
        probabilities[destination] = probability

    return probabilities


def normalizeWeights(weights: dict[str, float]) -> dict[str, float]:
    totalWeight = sum(weights.values())
    if totalWeight <= 0:
        raise ValueError("Weights must sum to a positive value.")

    destinations = sorted(weights.keys(), key=locationSortKey)
    probabilities: dict[str, float] = {}

    runningSum = 0.0
    for index, destination in enumerate(destinations):
        if index == len(destinations) - 1:
            probabilities[destination] = round(1.0 - runningSum, 12)
        else:
            probability = round(weights[destination] / totalWeight, 12)
            probabilities[destination] = probability
            runningSum += probability

    return probabilities


def enforce_min_transition_prob_on_model(
    modelData: dict,
    keyLocations: KeyLocations,
    min_prob: float,
    escape_prob: float,
) -> None:
    """Ensure each outgoing destination has at least `min_prob` probability.
    If probabilities violate the threshold and `escape_prob` > 0, add a tiny-probability
    fallback to the safe sink on the same edge (and try to reset clocks/delays).
    Otherwise raise ValueError to indicate an invalid generated model.
    """
    automaton = modelData["automata"][0]
    variables = automaton.get("variables", [])
    var_types = {v["name"]: v.get("type") for v in variables}

    for edge in automaton.get("edges", []):
        destinations = edge.get("destinations", [])
        if not destinations:
            continue

        probs = [float(dest.get("probability", {}).get("exp", 1.0)) for dest in destinations]

        # If any probability is negative, fail immediately
        for p in probs:
            if p < 0:
                raise ValueError("Negative transition probability in generated model.")

        # If all probabilities are effectively zero, attempt to add escape or fail
        total = sum(probs)
        if total <= 0.0:
            if escape_prob and escape_prob > 0.0:
                # append a fallback destination to safe sink
                guard_expr = edge.get("guard", {}).get("exp")
                refs = expressionVariableReferences(guard_expr)
                clock_ref = next((r for r in refs if var_types.get(r) == "clock"), None)
                delay_ref = next((r for r in refs if var_types.get(r) == "real"), None)
                assignment_list = [{"ref": RISK_VARIABLE_NAME, "value": 0}]
                if clock_ref:
                    assignment_list.append({"ref": clock_ref, "value": 0})
                if delay_ref:
                    assignment_list.append({"ref": delay_ref, "value": 0})

                destinations.append(
                    {
                        "location": keyLocations.safeSink,
                        "probability": {"exp": float(escape_prob)},
                        "assignments": assignment_list,
                    }
                )
                probs = [float(dest.get("probability", {}).get("exp", 0.0)) for dest in destinations]
                total = sum(probs)
            else:
                raise ValueError(
                    "All outgoing transition probabilities are zero for an edge; set --escape_prob>0 to add a tiny fallback."
                )

        for p in probs:
            if p < min_prob:
                raise ValueError(
                    f"Transition probability {p} is below the configured minimum {min_prob}."
                )

    # Conservative static check: ensure guards referencing clock >= delay are satisfiable
    # by checking min possible delay <= max possible invariant bound for that location.
    # Build maps of incoming assignments for delay variables and automaton variable defaults.
    var_initials: dict[str, object] = {}
    for var in automaton.get("variables", []):
        name = var.get("name")
        if name:
            var_initials[name] = var.get("initial-value")

    # Helper to compute min/max for an assignment expression
    def sample_bounds_from_expr(value_expr: object) -> tuple[float, float]:
        if value_expr is None:
            return (0.0, math.inf)
        if isinstance(value_expr, (int, float)):
            v = float(value_expr)
            return (v, v)
        if isinstance(value_expr, dict):
            dist = value_expr.get("distribution")
            args = value_expr.get("args")
            if dist == "Uniform" and isinstance(args, list) and len(args) >= 2:
                low = float(args[0])
                high = float(args[1])
                return (low, high)
            if dist == "Exponential":
                # Exponential support is (0, inf)
                return (0.0, math.inf)
            # If expression is an arithmetic expression, try to evaluate numerically if constants
            if "op" in value_expr:
                # attempt to resolve simple division of two integers in form {'op':'/','left':a,'right':b}
                if value_expr.get("op") == "/":
                    left = value_expr.get("left")
                    right = value_expr.get("right")
                    try:
                        if left is not None and right is not None:
                            l = float(left)
                            r = float(right)
                            if r != 0:
                                return (l / r, l / r)
                    except Exception:
                        pass
            return (0.0, math.inf)
        return (0.0, math.inf)

    # Gather incoming assignments per location for delay vars
    incoming_delay_bounds: dict[str, tuple[float, float]] = {}
    # initialize from automaton variable defaults
    for varname, init_val in var_initials.items():
        if varname.startswith("x_"):
            incoming_delay_bounds[varname] = sample_bounds_from_expr(init_val)

    for edge in automaton.get("edges", []):
        for dest in edge.get("destinations", []):
            for assignment in dest.get("assignments", []):
                ref = assignment.get("ref")
                val = assignment.get("value")
                if isinstance(ref, str) and ref.startswith("x_"):
                    low, high = sample_bounds_from_expr(val)
                    prev = incoming_delay_bounds.get(ref)
                    if prev is None:
                        incoming_delay_bounds[ref] = (low, high)
                    else:
                        incoming_delay_bounds[ref] = (min(prev[0], low), max(prev[1], high))

    # Helper to compute invariant max bound for a location's clock
    def invariant_max_bound(location_data: dict) -> float:
        timeprog = location_data.get("time-progress", {}).get("exp")
        if timeprog is None:
            return math.inf

        # collect all OP_LE where left is a clock name and right is numeric or delay var
        bounds: list[float] = []

        def walk(expr: object):
            if not isinstance(expr, dict):
                return
            op = expr.get("op")
            if op == OP_LE:
                left = expr.get("left")
                right = expr.get("right")
                if isinstance(right, (int, float)):
                    bounds.append(float(right))
                elif isinstance(right, str) and right.startswith("x_"):
                    b = incoming_delay_bounds.get(right)
                    if b is not None:
                        bounds.append(b[1])
                    else:
                        bounds.append(math.inf)
            for v in expr.values():
                if isinstance(v, (dict, list)):
                    if isinstance(v, dict):
                        walk(v)
                    else:
                        for it in v:
                            walk(it)

        walk(timeprog)
        if not bounds:
            return math.inf
        return min(bounds)

    # For each non-absorbing location, check guards
    location_map = {loc["name"]: loc for loc in automaton.get("locations", [])}
    for edge in automaton.get("edges", []):
        source = edge.get("location")
        if source in {keyLocations.failure, keyLocations.safeSink}:
            continue

        # detect if guard contains clock >= some delay var
        guard = edge.get("guard", {}).get("exp")
        if not isinstance(guard, dict):
            continue

        def find_ge(expr: object):
            if not isinstance(expr, dict):
                return None
            if expr.get("op") == OP_GE:
                left = expr.get("left")
                right = expr.get("right")
                if isinstance(left, str) and isinstance(right, str) and left.startswith("c_") and right.startswith("x_"):
                    return (left, right)
            for v in expr.values():
                if isinstance(v, dict):
                    res = find_ge(v)
                    if res:
                        return res
                elif isinstance(v, list):
                    for it in v:
                        res = find_ge(it)
                        if res:
                            return res
            return None

        ge = find_ge(guard)
        if not ge:
            continue

        clock_name, delay_name = ge

        min_delay, _ = incoming_delay_bounds.get(delay_name, (0.0, math.inf))
        max_inv = invariant_max_bound(location_map.get(source, {}))

        if min_delay > max_inv + 1e-12:
            if escape_prob and escape_prob > 0.0:
                # add fallback transition from source to safe sink with escape_prob
                # find any existing edge entry for this source and append destination
                # append only once per source
                appended = False
                for dest in edge.get("destinations", []):
                    if dest.get("location") == keyLocations.safeSink:
                        appended = True
                        break
                if not appended:
                    edge["destinations"].append(
                        {
                            "location": keyLocations.safeSink,
                            "probability": {"exp": float(escape_prob)},
                            "assignments": [{"ref": RISK_VARIABLE_NAME, "value": 0}, {"ref": clock_name, "value": 0}],
                        }
                    )
            else:
                raise ValueError(
                    f"Potential time-lock detected at location '{source}': min delay {min_delay} > invariant bound {max_inv}"
                )


def runSamplingFeasibilityCheck(
    modelData: dict,
    params: GenerationParams,
    keyLocations: KeyLocations,
    sampleCount: int = 128,
) -> None:
    """Monte Carlo sanity check: each non-absorbing location should admit at least one sampled delay value
    that does not exceed the location's invariant upper bound.
    This is conservative and deterministic for a given model seed.
    """
    automaton = modelData["automata"][0]
    location_map = {location["name"]: location for location in automaton.get("locations", [])}
    variable_map = {variable["name"]: variable for variable in automaton.get("variables", [])}

    def sample_from_initial_value(initial_value: object, rng: random.Random) -> float:
        if isinstance(initial_value, (int, float)):
            return float(initial_value)
        if isinstance(initial_value, dict):
            distribution = initial_value.get("distribution")
            args = initial_value.get("args", [])
            if distribution == "Uniform" and isinstance(args, list) and len(args) >= 2:
                return float(rng.uniform(float(args[0]), float(args[1])))
            if distribution == "Exponential" and isinstance(args, list) and args:
                rate_expr = args[0]
                if isinstance(rate_expr, dict) and rate_expr.get("op") == "/":
                    left = rate_expr.get("left")
                    right = rate_expr.get("right")
                    try:
                        if left is not None and right is not None:
                            rate = float(left) / float(right)
                            if rate > 0:
                                return float(rng.expovariate(rate))
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
        return 0.0

    def location_upper_bound(location_name: str) -> float:
        location = location_map.get(location_name)
        if not location or location_name in {keyLocations.failure, keyLocations.safeSink}:
            return math.inf

        invariant = location.get("time-progress", {}).get("exp")

        def scan(expr: object) -> list[float]:
            if expr is None:
                return []
            if isinstance(expr, (int, float)):
                return [float(expr)]
            if isinstance(expr, list):
                bounds: list[float] = []
                for item in expr:
                    bounds.extend(scan(item))
                return bounds
            if not isinstance(expr, dict):
                return []

            bounds: list[float] = []
            if expr.get("op") == OP_LE:
                right = expr.get("right")
                if isinstance(right, (int, float)):
                    bounds.append(float(right))
            for value in expr.values():
                if isinstance(value, (dict, list)):
                    bounds.extend(scan(value))
            return bounds

        bounds = scan(invariant)
        return min(bounds) if bounds else math.inf

    sampled_rng = random.Random(params.seed ^ 0x5A17)
    location_names = [location["name"] for location in automaton.get("locations", [])]
    active_locations = [name for name in location_names if name not in {keyLocations.failure, keyLocations.safeSink}]
    locationDelayMap: dict[str, str] = {}
    active_clock_map = assignClocksToLocations(active_locations, params.numClocks)
    for location_name, clock_index in active_clock_map.items():
        locationDelayMap[location_name] = f"x_{clock_index}"

    failures: list[str] = []
    for location_name, delay_name in locationDelayMap.items():
        upper_bound = location_upper_bound(location_name)
        initial_value = variable_map.get(delay_name, {}).get("initial-value")

        enabled = False
        for _ in range(sampleCount):
            sample_value = sample_from_initial_value(initial_value, sampled_rng)
            if sample_value <= upper_bound + 1e-12:
                enabled = True
                break

        if not enabled:
            failures.append(
                f"{location_name} via {delay_name} (sampled delays always exceed invariant bound {upper_bound})"
            )

    if failures:
        raise ValueError(
            "Sampling feasibility check failed for the following locations: " + "; ".join(failures)
        )


def buildAssignments(
    source: str,
    destination: str,
    keyLocations: KeyLocations,
    clockName: str,
    delayName: str,
    params: GenerationParams,
    rng: random.Random,
) -> list[dict]:
    assignments: list[dict] = []

    if destination == keyLocations.failure:
        assignments.append({"ref": FAILURE_VARIABLE_NAME, "value": True})
        assignments.append({"ref": RISK_VARIABLE_NAME, "value": RISK_MAX})
    elif destination == keyLocations.safeSink:
        assignments.append({"ref": RISK_VARIABLE_NAME, "value": 0})
    elif destination in {keyLocations.gatewayA, keyLocations.gatewayB}:
        assignments.append({"ref": RISK_VARIABLE_NAME, "value": buildIncreaseRiskExpression()})
    else:
        assignments.append({"ref": RISK_VARIABLE_NAME, "value": buildDecreaseRiskExpression()})

    assignments.append({"ref": clockName, "value": 0})
    assignments.append(
        {
            "ref": delayName,
            "value": buildDelayDistribution(source, destination, params, rng),
        }
    )

    return assignments


def buildIncreaseRiskExpression() -> dict:
    return {
        "op": "ite",
        "if": {
            "op": "<",
            "left": RISK_VARIABLE_NAME,
            "right": RISK_MAX,
        },
        "then": {
            "op": "+",
            "left": RISK_VARIABLE_NAME,
            "right": 1,
        },
        "else": RISK_VARIABLE_NAME,
    }


def buildDecreaseRiskExpression() -> dict:
    return {
        "op": "ite",
        "if": {
            "op": ">",
            "left": RISK_VARIABLE_NAME,
            "right": 0,
        },
        "then": {
            "op": "-",
            "left": RISK_VARIABLE_NAME,
            "right": 1,
        },
        "else": RISK_VARIABLE_NAME,
    }


def buildDelayDistribution(source: str, destination: str, params: GenerationParams, rng: random.Random) -> dict:
    maxBound = max(2, int(round(params.maxTimeBound)))

    if destination == FAILURE_LOCATION_NAME or source in {"loc_3", "loc_5"}:
        low = 1
        high = max(2, int(maxBound * 0.45))
        if high <= low:
            high = low + 1
        return {
            "distribution": "Uniform",
            "args": [low, high],
        }

    if rng.random() < 0.7:
        low = rng.randint(1, max(1, int(maxBound * 0.6)))
        high = rng.randint(max(low + 1, 2), maxBound)
        return {
            "distribution": "Uniform",
            "args": [low, high],
        }

    numerator = rng.randint(1, max(2, int(maxBound * 0.4)))
    denominator = max(1, maxBound)
    return {
        "distribution": "Exponential",
        "args": [
            {
                "op": "/",
                "left": numerator,
                "right": denominator,
            }
        ],
    }


def buildAutomatonVariables(
    clockNames: list[str],
    delayNames: list[str],
    params: GenerationParams,
    rng: random.Random,
) -> list[dict]:
    variables: list[dict] = []

    maxBound = max(2, int(round(params.maxTimeBound)))

    for clockName, delayName in zip(clockNames, delayNames):
        variables.append(
            {
                "name": clockName,
                "type": "clock",
                "initial-value": 0,
            }
        )

        low = rng.randint(1, max(1, int(maxBound * 0.5)))
        high = rng.randint(max(low + 1, 2), maxBound)
        delayVariable = {
            "name": delayName,
            "type": "real",
            "initial-value": {
                "distribution": "Uniform",
                "args": [low, high],
            },
        }
        variables.append(delayVariable)

    return variables


def validateModelStructure(
    modelData: dict,
    params: GenerationParams,
    keyLocations: KeyLocations,
    clockNames: list[str],
) -> None:
    automaton = modelData["automata"][0]
    locations = automaton["locations"]
    edges = automaton["edges"]

    locationNames = {location["name"] for location in locations}
    if keyLocations.failure not in locationNames:
        raise ValueError("Generated model is missing the designated failure location.")

    if keyLocations.safeSink not in locationNames:
        raise ValueError("Generated model is missing the designated safe sink location.")

    outgoingByLocation = {locationName: [] for locationName in locationNames}
    incomingByLocation = {locationName: [] for locationName in locationNames}

    for edge in edges:
        source = edge["location"]
        if source not in locationNames:
            raise ValueError(f"Edge source '{source}' is not a declared location.")

        destinations = edge.get("destinations", [])
        if not destinations:
            raise ValueError(f"Edge from '{source}' has no destinations.")

        probabilitySum = 0.0
        for destination in destinations:
            target = destination["location"]
            if target not in locationNames:
                raise ValueError(f"Edge destination '{target}' is not a declared location.")

            probabilityExpression = destination.get("probability", {}).get("exp", 1.0)
            if not isinstance(probabilityExpression, (int, float)):
                raise ValueError("This generator expects numeric probabilities for validation.")
            if probabilityExpression < 0:
                raise ValueError("Probabilities must be non-negative.")

            probabilitySum += float(probabilityExpression)
            outgoingByLocation[source].append(target)
            incomingByLocation[target].append(source)

        if not math.isclose(probabilitySum, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"Probabilities from source '{source}' must sum to 1.0. Got {probabilitySum}.")

    absorbingAllowed = {keyLocations.failure, keyLocations.safeSink}
    for locationName in locationNames:
        if locationName in absorbingAllowed:
            continue
        if len(outgoingByLocation[locationName]) == 0:
            raise ValueError(f"Found deadlock at non-absorbing location '{locationName}'.")

    if outgoingByLocation[keyLocations.failure]:
        raise ValueError("Failure location must be absorbing with no outgoing edges.")

    if outgoingByLocation[keyLocations.safeSink]:
        raise ValueError("Safe sink location must be absorbing with no outgoing edges.")

    if not incomingByLocation[keyLocations.safeSink]:
        raise ValueError("Safe sink must be reachable from at least one non-absorbing location.")

    reachable = computeReachableLocations(automaton["initial-locations"], outgoingByLocation)
    if keyLocations.failure not in reachable:
        raise ValueError("Failure location is not reachable from the initial location.")

    reachableFailureGateways = {
        source
        for source in incomingByLocation[keyLocations.failure]
        if source in reachable
    }
    if len(reachableFailureGateways) < 2:
        raise ValueError("Generated model must provide at least two reachable alternative paths into failure.")

    validateClockUsage(automaton, clockNames)
    validateRequiredModelSize(params, automaton)


def validateRequiredModelSize(params: GenerationParams, automaton: dict) -> None:
    if len(automaton["locations"]) != params.numStates:
        raise ValueError("Generated location count does not match num_states.")

    clockCount = sum(1 for variable in automaton["variables"] if variable["type"] == "clock")
    if clockCount != params.numClocks:
        raise ValueError("Generated clock count does not match num_clocks.")


def validateClockUsage(automaton: dict, clockNames: list[str]) -> None:
    invariantUsage: set[str] = set()
    guardUsage: set[str] = set()
    resetUsage: set[str] = set()

    for location in automaton["locations"]:
        timeProgress = location.get("time-progress", {}).get("exp")
        invariantUsage.update(clockNamesUsedInExpression(timeProgress, set(clockNames)))

    for edge in automaton["edges"]:
        guardExpression = edge.get("guard", {}).get("exp")
        guardUsage.update(clockNamesUsedInExpression(guardExpression, set(clockNames)))

        for destination in edge.get("destinations", []):
            for assignment in destination.get("assignments", []):
                ref = assignment.get("ref")
                if ref in clockNames:
                    resetUsage.add(ref)

    missingInvariant = sorted(set(clockNames) - invariantUsage)
    missingGuard = sorted(set(clockNames) - guardUsage)
    missingReset = sorted(set(clockNames) - resetUsage)

    if missingInvariant:
        raise ValueError(f"Each clock must appear in invariants. Missing: {missingInvariant}")
    if missingGuard:
        raise ValueError(f"Each clock must appear in guards. Missing: {missingGuard}")
    if missingReset:
        raise ValueError(f"Each clock must appear in resets. Missing: {missingReset}")


def clockNamesUsedInExpression(expression: object, validClockNames: set[str]) -> set[str]:
    foundReferences = expressionVariableReferences(expression)
    return {name for name in foundReferences if name in validClockNames}


def expressionVariableReferences(expression: object) -> set[str]:
    if expression is None:
        return set()

    if isinstance(expression, str):
        return {expression}

    if isinstance(expression, (int, float, bool)):
        return set()

    if isinstance(expression, list):
        names: set[str] = set()
        for item in expression:
            names.update(expressionVariableReferences(item))
        return names

    if not isinstance(expression, dict):
        return set()

    if "value" in expression and len(expression) == 1:
        return expressionVariableReferences(expression["value"])

    names: set[str] = set()
    for key, value in expression.items():
        if key in {"op", "distribution", "kind", "base", "name", "type", "ref", "fun"}:
            continue
        names.update(expressionVariableReferences(value))
    return names


def computeReachableLocations(initialLocations: list[str], outgoingByLocation: dict[str, list[str]]) -> set[str]:
    pending = list(initialLocations)
    visited: set[str] = set(initialLocations)

    while pending:
        source = pending.pop()
        for destination in outgoingByLocation.get(source, []):
            if destination not in visited:
                visited.add(destination)
                pending.append(destination)

    return visited


def locationSortKey(locationName: str) -> int:
    if locationName == SAFE_SINK_LABEL:
        return 10**9

    if locationName.startswith("loc_"):
        suffix = locationName.split("_", maxsplit=1)[1]
        if suffix.isdigit():
            return int(suffix)

    return 10**9 - 1


def writeModelFile(modelData: dict, outputDir: Path) -> Path:
    outputDir.mkdir(parents=True, exist_ok=True)
    outputPath = outputDir / f"{modelData['name']}.jani"

    with outputPath.open("w", encoding="utf-8") as handle:
        json.dump(modelData, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    return outputPath


def canonicalJson(modelData: dict) -> str:
    return json.dumps(modelData, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def runDeterminismCheck(
    params: GenerationParams,
    modelPrefix: str,
    modelIndex: int,
    min_transition_prob: float = DEFAULT_MIN_TRANSITION_PROB,
    escape_prob: float = DEFAULT_ESCAPE_PROB,
) -> None:
    first = buildBenchmarkModel(params, modelPrefix, modelIndex, min_transition_prob, escape_prob)
    second = buildBenchmarkModel(params, modelPrefix, modelIndex, min_transition_prob, escape_prob)

    if canonicalJson(first) != canonicalJson(second):
        raise RuntimeError(
            "Determinism check failed: repeated generation with same parameters produced different models."
        )


def formatSummaryRow(
    outputPath: Path,
    params: GenerationParams,
    dryRun: bool,
) -> str:
    status = "DRY-RUN" if dryRun else "WROTE"
    return (
        f"[{status}] {outputPath.name} | "
        f"num_states={params.numStates}, "
        f"num_clocks={params.numClocks}, "
        f"branching_factor={params.branchingFactor}, "
        f"max_time_bound={params.maxTimeBound}, "
        f"rare_event_probability={params.rareEventProbability}, "
        f"seed={params.seed}"
    )


def main() -> None:
    cliArgs = parseCliArgs(__import__("sys").argv[1:])
    parameterGrid = buildParameterGrid(cliArgs)

    outputDir = Path(cliArgs.output_dir)
    summaryRows: list[str] = []

    for modelIndex, params in enumerate(parameterGrid):
        if cliArgs.determinism_check:
            runDeterminismCheck(
                params,
                cliArgs.model_prefix,
                modelIndex,
                cliArgs.min_transition_prob,
                cliArgs.escape_prob,
            )

        modelData = buildBenchmarkModel(
            params,
            cliArgs.model_prefix,
            modelIndex,
            cliArgs.min_transition_prob,
            cliArgs.escape_prob,
        )

        if cliArgs.dry_run:
            outputPath = outputDir / f"{modelData['name']}.jani"
        else:
            outputPath = writeModelFile(modelData, outputDir)

        summaryRows.append(formatSummaryRow(outputPath, params, cliArgs.dry_run))

    print(f"Generated {len(summaryRows)} benchmark model(s).")
    for row in summaryRows:
        print(row)


if __name__ == "__main__":
    main()
