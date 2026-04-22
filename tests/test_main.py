import subprocess

import pytest

import main

pytestmark = pytest.mark.skip(reason="Tests not up to date - needs update")

def test_parseMemoryArg_missing_raisesSystemExit():
    with pytest.raises(SystemExit) as error:
        main.parseMemoryArg(["main.py"])

    assert error.value.code == 1


def test_parseMemoryArg_invalid_raisesSystemExit():
    with pytest.raises(SystemExit) as error:
        main.parseMemoryArg(["main.py", "-m", "0"])

    assert error.value.code == 1


def test_parseModelArg_returnsNone_whenMissing():
    value = main.parseModelArg(["main.py", "-m", "100"])
    assert value is None


def test_parseModelArg_returnsPath_whenProvided(tmp_path):
    model = tmp_path / "model.jani"
    model.write_text("{}", encoding="utf-8")

    value = main.parseModelArg(["main.py", "-m", "100", "--model", str(model)])
    assert value == str(model)


def test_parseModelArg_raises_forMissingFile(tmp_path):
    model = tmp_path / "missing.jani"

    with pytest.raises(SystemExit) as error:
        main.parseModelArg(["main.py", "-m", "100", "--model", str(model)])

    assert error.value.code == 1


def test_parseCpuArg_returnsNone_whenMissing():
    value = main.parseCpuArg(["main.py", "-m", "100"])
    assert value is None


def test_parseCpuArg_returnsFloat_whenProvided():
    value = main.parseCpuArg(["main.py", "-m", "100", "--cpus", "1.5"])
    assert value == 1.5


def test_parseCpuArg_raises_forInvalidValue():
    with pytest.raises(SystemExit) as error:
        main.parseCpuArg(["main.py", "-m", "100", "--cpus", "0"])

    assert error.value.code == 1


def test_ensureDockerEngineAvailable_raises_whenDockerMissing(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as error:
        main.ensureDockerEngineAvailable()

    assert error.value.code == 1


def test_ensureDockerEngineAvailable_raises_whenDaemonUnavailable(monkeypatch):
    result = subprocess.CompletedProcess(args=["docker", "info"], returncode=1, stdout="", stderr="daemon unavailable")

    monkeypatch.setattr(main.subprocess, "run", lambda *_args, **_kwargs: result)

    with pytest.raises(SystemExit) as error:
        main.ensureDockerEngineAvailable()

    assert error.value.code == 1


def test_ensureDockerEngineAvailable_passes_whenHealthy(monkeypatch):
    result = subprocess.CompletedProcess(args=["docker", "info"], returncode=0, stdout="ok", stderr="")
    monkeypatch.setattr(main.subprocess, "run", lambda *_args, **_kwargs: result)

    main.ensureDockerEngineAvailable()


def test_runDocker_buildsExpectedCommand(tmp_path, monkeypatch):
    model = tmp_path / "model.jani"
    model.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main, "HOSTRESULTS", str(tmp_path / "results"))

    seen = {}

    def fake_run(command):
        seen["command"] = command
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    main.runDocker(520, str(model))

    command = seen["command"]
    assert command[0:3] == ["docker", "run", "--rm"]
    assert "-m" in command
    assert "520m" in command
    assert "simulation-image" in command
    assert f"/input/{model.name}" in command


def test_runDocker_withCpuLimit_buildsExpectedCommand(tmp_path, monkeypatch):
    model = tmp_path / "model.jani"
    model.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(main, "HOSTRESULTS", str(tmp_path / "results"))

    seen = {}

    def fake_run(command):
        seen["command"] = command
        return subprocess.CompletedProcess(args=command, returncode=0)

    monkeypatch.setattr(main.subprocess, "run", fake_run)

    main.runDocker(520, str(model), 1.25)

    command = seen["command"]
    assert command[0:3] == ["docker", "run", "--rm"]
    assert "--cpus" in command
    assert "1.25" in command
    assert "-m" in command
    assert "520m" in command


def test_main_usesProvidedModel_withoutInteractiveSelection(tmp_path, monkeypatch):
    model = tmp_path / "model.jani"
    model.write_text("{}", encoding="utf-8")

    called = {}

    monkeypatch.setattr(main, "parseMemoryArg", lambda _args: 200)
    monkeypatch.setattr(main, "parseModelArg", lambda _args: str(model))
    monkeypatch.setattr(main, "ensureDockerEngineAvailable", lambda: called.setdefault("preflight", True))
    monkeypatch.setattr(main, "runDocker", lambda memory, modelPath: called.update({"memory": memory, "modelPath": modelPath}))

    def should_not_be_called(*_args, **_kwargs):
        raise AssertionError("Interactive selection should not be called when --model is provided")

    monkeypatch.setattr(main, "retrieveModelNames", should_not_be_called)
    monkeypatch.setattr(main, "selectModels", should_not_be_called)

    main.main()

    assert called["preflight"] is True
    assert called["memory"] == 200
    assert called["modelPath"] == str(model.resolve())


def test_main_usesInteractiveSelection_whenModelNotProvided(monkeypatch):
    called = {}
    selected = "models/benchmark/jani/chain-sta.jani"

    monkeypatch.setattr(main, "parseMemoryArg", lambda _args: 300)
    monkeypatch.setattr(main, "parseModelArg", lambda _args: None)
    monkeypatch.setattr(main, "ensureDockerEngineAvailable", lambda: called.setdefault("preflight", True))
    monkeypatch.setattr(main, "retrieveModelNames", lambda: [selected])
    monkeypatch.setattr(main, "selectModels", lambda _models: selected)
    monkeypatch.setattr(main, "runDocker", lambda memory, modelPath: called.update({"memory": memory, "modelPath": modelPath}))

    main.main()

    assert called["preflight"] is True
    assert called["memory"] == 300
    assert called["modelPath"].endswith("chain-sta.jani")
