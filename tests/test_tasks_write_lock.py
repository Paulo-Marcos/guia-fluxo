"""D-208: criar demanda e montar o lote do Dependabot passam pela trava do tasks.json.

A D-204 trancou o `save_task`; ficaram de fora a criacao (`_cli_creation`) e o
lote (`_dependabot`), que liam-mudavam-gravavam sem trava: dois processos ao
mesmo tempo (o chat criando, o executor montando o lote) e o segundo a gravar
apagava a demanda do primeiro.

O driver de cada processo espera um instante comum e alarga a janela do
"ler" (dorme logo depois de ler o tasks.json), para a corrida acontecer sempre
e nao so de vez em quando.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from conftest_paths import CORE_LOCK, CORE_SRC

PROCESSES = 6

DRIVER = textwrap.dedent(
    """
    import runpy, sys, time
    sys.path.insert(0, "core/src")
    sys.path.insert(0, "core/lock")
    import _state

    _read = _state.read_json
    def slow_read(path, default):
        value = _read(path, default)
        if path.name == "tasks.json":
            time.sleep(0.3)
        return value
    _state.read_json = slow_read

    time.sleep(max(0.0, float(sys.argv[1]) - time.time()))
    mode = sys.argv[2]
    if mode == "lote":
        import _dependabot
        _dependabot.create_lote({"bumps": [{"number": 7}], "security": False})
    else:
        sys.argv = ["guia.py", *sys.argv[3:]]
        runpy.run_path("core/src/guia.py", run_name="__main__")
    """
)


class TasksWriteLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.sb = Path(self._tmp.name)
        (self.sb / "core" / "src").mkdir(parents=True)
        (self.sb / "core" / "lock").mkdir(parents=True)
        for src in CORE_SRC.glob("*.py"):
            if not src.name.startswith("__"):
                shutil.copy2(src, self.sb / "core" / "src" / src.name)
        shutil.copy2(CORE_LOCK / "lock_api.py", self.sb / "core" / "lock" / "lock_api.py")
        (self.sb / ".guia").mkdir()
        (self.sb / "driver.py").write_text(DRIVER, encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def _race(self, *jobs: tuple[str, ...]) -> list[dict]:
        start = time.time() + 2.0
        procs = [
            subprocess.Popen([sys.executable, "driver.py", str(start), *job], cwd=self.sb,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for job in jobs
        ]
        for proc in procs:
            _, err = proc.communicate(timeout=120)
            self.assertEqual(proc.returncode, 0, msg=err)
        data = json.loads((self.sb / ".guia" / "tasks.json").read_text(encoding="utf-8"))
        return data["tasks"]

    def test_criacoes_simultaneas_ficam_todas(self) -> None:
        tasks = self._race(*[("cli", "backlog", "add", f"ideia {n}") for n in range(PROCESSES)])
        self.assertEqual(len(tasks), PROCESSES, msg=[t["title"] for t in tasks])
        self.assertEqual(len({t["id"] for t in tasks}), PROCESSES)

    def test_lote_do_dependabot_nao_apaga_criacao_simultanea(self) -> None:
        tasks = self._race(("lote",), ("cli", "backlog", "add", "ideia a"), ("cli", "backlog", "add", "ideia b"))
        self.assertEqual(len(tasks), 3, msg=[t["title"] for t in tasks])
        self.assertEqual(len({t["id"] for t in tasks}), 3)


if __name__ == "__main__":
    unittest.main()
