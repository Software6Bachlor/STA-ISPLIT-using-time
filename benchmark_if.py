from __future__ import annotations

import argparse
import csv
import io
import itertools
import logging
import multiprocessing as mp
import os
import sys
import threading
import tracemalloc
import traceback
import time
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

from generateJaniBenchmarks import GenerationParams, buildBenchmarkModel, parseSweepValues
from importanceFunctionBuilder import ImportanceFunctionBuilder
from parser import parseModel


MB = 1024 * 1024
DEFAULT_RARE_LOCATION = "loc_0"
DEFAULT_MEMORY_MB = 4096
DEFAULT_MODEL_PREFIX = "if-benchmark"
DEFAULT_REPORT_FILE = Path("results/if-benchmark/if_benchmark_results.csv")
REPORT_FIELDNAMES = [
    "family",
    "model_name",
    "model_path",
    "num_states",
    "num_clocks",
    "branching_factor",
    "max_time_bound",
    "rare_event_probability",
    "seed",
    "build_status",
    "build_seconds",
    "rss_before_mb",
    "rss_after_mb",
    "peak_rss_mb",
    "time_distance_locations",
    "hop_distance_locations",
    "state_classes_explored",
]


@dataclass(frozen=True, slots=True)
class FamilyConfig:
    name: str
    numStates: str
    numClocks: str
    branchingFactor: str
    maxTimeBound: str
    rareEventProbability: str
    seeds: str


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    family: str
    modelName: str
    modelPath: str
    numStates: int
    numClocks: int
    branchingFactor: float
    maxTimeBound: float
    rareEventProbability: float
    seed: int
    buildStatus: str
    buildSeconds: float
    rssBeforeMb: float
    rssAfterMb: float
    peakRssMb: float
    timeDistanceLocations: int
    hopDistanceLocations: int
    stateClassesExplored: int


@dataclass(frozen=True, slots=True)
class SweepSummary:
    family: str
    numStates: list[int]
    numClocks: list[int]
    branchingFactors: list[float]
    maxTimeBounds: list[float]
    rareEventProbabilities: list[float]
    seeds: list[int]


def formatValues(values: list[object], limit: int = 8) -> str:
    if not values:
        return "[]"

    if len(values) <= limit:
        return "[" + ", ".join(str(value) for value in values) + "]"

    shown = ", ".join(str(value) for value in values[: limit - 1])
    return f"[{shown}, ... ({len(values)} total)]"


def formatFloat(value: float, digits: int = 3) -> str:
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return text if text else "0"


def printFamilySummary(summary: SweepSummary) -> None:
    print(f"[PLAN] {summary.family}")
    print(f"  num_states           = {formatValues(summary.numStates)}")
    print(f"  num_clocks           = {formatValues(summary.numClocks)}")
    print(f"  branching_factor     = {formatValues(summary.branchingFactors)}")
    print(f"  max_time_bound       = {formatValues(summary.maxTimeBounds)}")
    print(f"  rare_event_probability = {formatValues(summary.rareEventProbabilities)}")
    print(f"  seeds                = {formatValues(summary.seeds)}")


def printResultHeader() -> None:
    print()
    print(
        "[RESULT] family       model                              states clocks branch  time   seed  status      peak-rss  classes"
    )
    print(
        "[RESULT] ------------ --------------------------------- ------ ------ ------- ------ ----- ---------- --------- -------"
    )


def printResultRow(row: dict[str, object]) -> None:
    modelName = str(row["model_name"])
    if len(modelName) > 33:
        modelName = modelName[:30] + "..."

    print(
        f"[RESULT] {str(row['family']):<12} "
        f"{modelName:<33} "
        f"{int(row['num_states']):>6} "
        f"{int(row['num_clocks']):>6} "
        f"{formatFloat(float(row['branching_factor']), 2):>7} "
        f"{formatFloat(float(row['build_seconds']), 2):>6} "
        f"{int(row['seed']):>5} "
        f"{str(row['build_status']):<10} "
        f"{formatFloat(float(row['peak_rss_mb']), 1):>8} "
        f"{int(row['state_classes_explored']):>7}"
    )


def printErrorRow(family: str, params: GenerationParams, errorMessage: str) -> None:
    print(
        f"[ERROR] {family:<12} "
        f"states={params.numStates:<5} clocks={params.numClocks:<3} "
        f"branch={formatFloat(params.branchingFactor, 2):<5} "
        f"seed={params.seed:<5} {errorMessage}"
    )


def parseCliArgs(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate seeded STA benchmarks for the structural and temporal families, "
            "build the importance function, and record timing and memory metrics."
        )
    )
    parser.add_argument(
        "--family",
        choices=("structural", "temporal", "both"),
        default="both",
        help="Select which model family to run.",
    )
    parser.add_argument(
        "--structural-num-states",
        default="100:1000:100",
        help="Sweep for structural models: int, list, or range.",
    )
    parser.add_argument(
        "--structural-num-clocks",
        default="2:10:100",
        help="Clock sweep for structural models.",
    )
    parser.add_argument(
        "--structural-branching-factor",
        default="1:10:2.5",
        help="Branching-factor sweep for structural models.",
    )
    parser.add_argument(
        "--structural-max-time-bound",
        default="10",
        help="Time-bound sweep for structural models.",
    )
    parser.add_argument(
        "--structural-rare-event-probability",
        default="0.1",
        help="Failure probability sweep for structural models.",
    )
    parser.add_argument(
        "--temporal-num-states",
        default="100:1350:250",
        help="Sweep for temporal models: int, list, or range.",
    )
    parser.add_argument(
        "--temporal-num-clocks",
        default="1:10:2",
        help="Clock sweep for temporal models.",
    )
    parser.add_argument(
        "--temporal-branching-factor",
        default="2.0",
        help="Branching-factor sweep for temporal models.",
    )
    parser.add_argument(
        "--temporal-max-time-bound",
        default="10",
        help="Time-bound sweep for temporal models.",
    )
    parser.add_argument(
        "--temporal-rare-event-probability",
        default="0.1",
        help="Failure probability sweep for temporal models.",
    )
    parser.add_argument(
        "--seeds",
        default="1:5",
        help="Seed sweep shared by both families.",
    )
    parser.add_argument(
        "--memory-mb",
        type=int,
        default=DEFAULT_MEMORY_MB,
        help="Memory cap passed to ImportanceFunctionBuilder.",
    )
    parser.add_argument(
        "--if-time-limit",
        type=float,
        default=None,
        help="Optional time limit in seconds for the IF build.",
    )
    parser.add_argument(
        "--rare-location",
        default=DEFAULT_RARE_LOCATION,
        help="Rare-event location name used when constructing the IF.",
    )
    parser.add_argument(
        "--model-prefix",
        default=DEFAULT_MODEL_PREFIX,
        help="Prefix for generated model names.",
    )
    parser.add_argument(
        "--report-file",
        default=str(DEFAULT_REPORT_FILE),
        help="CSV file that receives the benchmark results.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the raw builder output for each run.",
    )
    return parser.parse_args(args[1:])


def buildFamilyConfigs(cliArgs: argparse.Namespace) -> list[FamilyConfig]:
    families: list[FamilyConfig] = []

    if cliArgs.family in {"structural", "both"}:
        families.append(
            FamilyConfig(
                name="structural",
                numStates=cliArgs.structural_num_states,
                numClocks=cliArgs.structural_num_clocks,
                branchingFactor=cliArgs.structural_branching_factor,
                maxTimeBound=cliArgs.structural_max_time_bound,
                rareEventProbability=cliArgs.structural_rare_event_probability,
                seeds=cliArgs.seeds,
            )
        )

    if cliArgs.family in {"temporal", "both"}:
        families.append(
            FamilyConfig(
                name="temporal",
                numStates=cliArgs.temporal_num_states,
                numClocks=cliArgs.temporal_num_clocks,
                branchingFactor=cliArgs.temporal_branching_factor,
                maxTimeBound=cliArgs.temporal_max_time_bound,
                rareEventProbability=cliArgs.temporal_rare_event_probability,
                seeds=cliArgs.seeds,
            )
        )

    return families


def expandFamilyParams(config: FamilyConfig) -> list[GenerationParams]:
    numStatesValues = [int(value) for value in parseSweepValues(config.numStates, int, f"{config.name}.num_states")]
    numClocksValues = [int(value) for value in parseSweepValues(config.numClocks, int, f"{config.name}.num_clocks")]
    branchingFactorValues = [
        float(value)
        for value in parseSweepValues(config.branchingFactor, float, f"{config.name}.branching_factor")
    ]
    maxTimeBoundValues = [
        float(value)
        for value in parseSweepValues(config.maxTimeBound, float, f"{config.name}.max_time_bound")
    ]
    rareEventProbabilityValues = [
        float(value)
        for value in parseSweepValues(config.rareEventProbability, float, f"{config.name}.rare_event_probability")
    ]
    seedValues = [int(value) for value in parseSweepValues(config.seeds, int, f"{config.name}.seed")]

    params: list[GenerationParams] = []
    for combination in itertools.product(
        numStatesValues,
        numClocksValues,
        branchingFactorValues,
        maxTimeBoundValues,
        rareEventProbabilityValues,
        seedValues,
    ):
        params.append(
            GenerationParams(
                numStates=combination[0],
                numClocks=combination[1],
                branchingFactor=combination[2],
                maxTimeBound=combination[3],
                rareEventProbability=combination[4],
                seed=combination[5],
            )
        )

    return params


def buildSweepSummary(config: FamilyConfig) -> SweepSummary:
    return SweepSummary(
        family=config.name,
        numStates=[int(value) for value in parseSweepValues(config.numStates, int, f"{config.name}.num_states")],
        numClocks=[int(value) for value in parseSweepValues(config.numClocks, int, f"{config.name}.num_clocks")],
        branchingFactors=[
            float(value) for value in parseSweepValues(config.branchingFactor, float, f"{config.name}.branching_factor")
        ],
        maxTimeBounds=[float(value) for value in parseSweepValues(config.maxTimeBound, float, f"{config.name}.max_time_bound")],
        rareEventProbabilities=[
            float(value)
            for value in parseSweepValues(config.rareEventProbability, float, f"{config.name}.rare_event_probability")
        ],
        seeds=[int(value) for value in parseSweepValues(config.seeds, int, f"{config.name}.seed")],
    )


class MemorySampler:
    def __init__(self, intervalSeconds: float = 0.05):
        self._intervalSeconds = intervalSeconds
        self._stopEvent = threading.Event()
        self.peakRssMb = 0.0
        self._thread = threading.Thread(target=self._run, daemon=True) if psutil is not None else None

    def __enter__(self) -> MemorySampler:
        if psutil is None:
            tracemalloc.start()
            currentMb = tracemalloc.get_traced_memory()[0] / MB
            self.peakRssMb = currentMb
            return self

        assert self._thread is not None
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if psutil is None:
            currentMb, peakMb = tracemalloc.get_traced_memory()
            self.peakRssMb = max(self.peakRssMb, peakMb / MB)
            tracemalloc.stop()
            return

        self._stopEvent.set()
        assert self._thread is not None
        self._thread.join()

    def _run(self) -> None:
        while not self._stopEvent.is_set():
            try:
                assert psutil is not None
                rssMb = psutil.Process().memory_info().rss / MB
            except psutil.Error:
                return

            if rssMb > self.peakRssMb:
                self.peakRssMb = rssMb

            self._stopEvent.wait(self._intervalSeconds)


class LoggerCapture:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._buffer = io.StringIO()
        self._handler = logging.StreamHandler(self._buffer)
        self._handler.setLevel(logging.WARNING)
        self._originalLevel = logger.level
        self._originalPropagate = logger.propagate

    def __enter__(self) -> io.StringIO:
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.WARNING)
        self._logger.propagate = False
        return self._buffer

    def __exit__(self, exc_type, exc, tb) -> None:
        self._logger.removeHandler(self._handler)
        self._logger.setLevel(self._originalLevel)
        self._logger.propagate = self._originalPropagate


def runSingleBenchmark(
    family: str,
    params: GenerationParams,
    modelPrefix: str,
    modelIndex: int,
    rareLocation: str,
    memoryMb: int,
    ifTimeLimit: float | None,
    verbose: bool,
) -> BenchmarkResult:
    modelData = buildBenchmarkModel(params, f"{modelPrefix}-{family}", modelIndex)
    modelPath = f"memory://{modelData['name']}"

    loadedModel = parseModel(modelData)
    if not loadedModel.automata:
        raise ValueError(f"Generated model {modelPath} does not contain any automata.")

    rssBeforeMb = getCurrentMemoryMb()

    builderLogger = logging.getLogger("importanceFunctionBuilder")
    outputBuffer = io.StringIO()
    with MemorySampler() as sampler:
        startTime = time.perf_counter()
        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(outputBuffer))
            stack.enter_context(redirect_stderr(outputBuffer))
            stack.enter_context(LoggerCapture(builderLogger))
            builder = ImportanceFunctionBuilder(
                loadedModel.automata[0],
                rareLocation,
                mbLimit=memoryMb,
                modelsVariables=loadedModel.variables,
                exponentialTruncationEpsilon=0.01,
                timeLimitSeconds=ifTimeLimit,
            )
            builder.build()
        buildSeconds = time.perf_counter() - startTime

    rssAfterMb = getCurrentMemoryMb()
    capturedOutput = outputBuffer.getvalue()
    if verbose and capturedOutput.strip():
        print(capturedOutput, end="")

    buildStatus = "completed"
    if "Memory limit approaching" in capturedOutput:
        buildStatus = "memory-limited"
    elif "Time limit of" in capturedOutput:
        buildStatus = "time-limited"

    timeDistanceLocations = len(builder.timeDistanceDict)
    hopDistanceLocations = len(builder.hopDistanceDict)
    stateClassesExplored = sum(len(stateClasses) for stateClasses in builder.timeDistanceDict.values())

    return BenchmarkResult(
        family=family,
        modelName=modelData["name"],
        modelPath=str(modelPath),
        numStates=params.numStates,
        numClocks=params.numClocks,
        branchingFactor=params.branchingFactor,
        maxTimeBound=params.maxTimeBound,
        rareEventProbability=params.rareEventProbability,
        seed=params.seed,
        buildStatus=buildStatus,
        buildSeconds=buildSeconds,
        rssBeforeMb=rssBeforeMb,
        rssAfterMb=rssAfterMb,
        peakRssMb=sampler.peakRssMb,
        timeDistanceLocations=timeDistanceLocations,
        hopDistanceLocations=hopDistanceLocations,
        stateClassesExplored=stateClassesExplored,
    )


def resultToRow(result: BenchmarkResult) -> dict[str, object]:
    return {
        "family": result.family,
        "model_name": result.modelName,
        "model_path": result.modelPath,
        "num_states": result.numStates,
        "num_clocks": result.numClocks,
        "branching_factor": result.branchingFactor,
        "max_time_bound": result.maxTimeBound,
        "rare_event_probability": result.rareEventProbability,
        "seed": result.seed,
        "build_status": result.buildStatus,
        "build_seconds": round(result.buildSeconds, 6),
        "rss_before_mb": round(result.rssBeforeMb, 3),
        "rss_after_mb": round(result.rssAfterMb, 3),
        "peak_rss_mb": round(result.peakRssMb, 3),
        "time_distance_locations": result.timeDistanceLocations,
        "hop_distance_locations": result.hopDistanceLocations,
        "state_classes_explored": result.stateClassesExplored,
    }


def ensureParentDirectory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def getCurrentMemoryMb() -> float:
    if psutil is not None:
        return psutil.Process().memory_info().rss / MB

    current, _peak = tracemalloc.get_traced_memory()
    return current / MB


def _benchmarkWorker(queue: mp.Queue, family: str, params: GenerationParams, modelPrefix: str, modelIndex: int, rareLocation: str, memoryMb: int, ifTimeLimit: float | None, verbose: bool) -> None:
    try:
        result = runSingleBenchmark(
            family=family,
            params=params,
            modelPrefix=modelPrefix,
            modelIndex=modelIndex,
            rareLocation=rareLocation,
            memoryMb=memoryMb,
            ifTimeLimit=ifTimeLimit,
            verbose=verbose,
        )
    except BaseException as exc:  # pragma: no cover - surfaced to parent process
        queue.put(
            {
                "ok": False,
                "family": family,
                "params": params,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
        return

    queue.put({"ok": True, "row": resultToRow(result)})


def runSingleBenchmarkInFreshProcess(
    family: str,
    params: GenerationParams,
    modelPrefix: str,
    modelIndex: int,
    rareLocation: str,
    memoryMb: int,
    ifTimeLimit: float | None,
    verbose: bool,
) -> dict[str, object]:
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    process = ctx.Process(
        target=_benchmarkWorker,
        args=(queue, family, params, modelPrefix, modelIndex, rareLocation, memoryMb, ifTimeLimit, verbose),
    )
    process.start()
    process.join()

    payload = queue.get() if not queue.empty() else None
    queue.close()
    queue.join_thread()

    if payload is None:
        raise RuntimeError(f"Benchmark process for family '{family}' exited with code {process.exitcode} and no result.")

    if not payload.get("ok"):
        errorMessage = payload.get("error", "unknown error")
        childTraceback = payload.get("traceback", "")
        raise RuntimeError(
            f"Benchmark failed for family '{family}' with num_states={params.numStates}, num_clocks={params.numClocks}, seed={params.seed}: {errorMessage}\n{childTraceback}"
        )

    return payload["row"]


def main() -> None:
    cliArgs = parseCliArgs(sys.argv)
    familyConfigs = buildFamilyConfigs(cliArgs)
    reportFile = Path(cliArgs.report_file)

    ensureParentDirectory(reportFile)
    resultCount = 0

    with reportFile.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()

        for familyConfig in familyConfigs:
            printFamilySummary(buildSweepSummary(familyConfig))

        for familyConfig in familyConfigs:
            parameterGrid = expandFamilyParams(familyConfig)
            print(f"[PLAN] {familyConfig.name}: {len(parameterGrid)} configuration(s)")
            printResultHeader()

            for modelIndex, params in enumerate(parameterGrid):
                row = runSingleBenchmarkInFreshProcess(
                    family=familyConfig.name,
                    params=params,
                    modelPrefix=cliArgs.model_prefix,
                    modelIndex=modelIndex,
                    rareLocation=cliArgs.rare_location,
                    memoryMb=cliArgs.memory_mb,
                    ifTimeLimit=cliArgs.if_time_limit,
                    verbose=cliArgs.verbose,
                )
                writer.writerow(row)
                handle.flush()
                resultCount += 1
                printResultRow(row)

    print()
    print(f"[DONE] Wrote {resultCount} result row(s) to {reportFile}")


if __name__ == "__main__":
    main()
