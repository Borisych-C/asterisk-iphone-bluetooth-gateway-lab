#!/usr/bin/env python3
"""Build the real patched listener function into a bounded socket harness."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

folder = Path(__file__).resolve().parent
source = (folder / "chan_mobile.c").read_text()
start = source.index("static void *do_sco_listen(void *data)\n{")
opening = source.index("{", start)
depth = 1
end = opening + 1
while depth:
    depth += (source[end] == "{") - (source[end] == "}")
    end += 1
function = source[start:end] + "\n"
(folder / "mobile_loop.inc").write_text(function)
results = {"source_sha256": hashlib.sha256(source.encode()).hexdigest(),
           "function_sha256": hashlib.sha256(function.encode()).hexdigest(),
           "compiler": subprocess.check_output(["cc", "--version"], text=True).splitlines()[0],
           "runs": []}
for name, options in (("optimized", ["-O2"]),
                      ("asan-ubsan", ["-O1", "-g", "-fsanitize=address,undefined",
                                     "-fno-omit-frame-pointer"])):
    binary = folder / ("listener-harness-" + name)
    command = ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pthread", *options,
               str(folder / "listener_harness.c"), "-o", str(binary)]
    subprocess.run(command, check=True)
    environment = os.environ.copy()
    environment["ASAN_OPTIONS"] = "detect_leaks=1:abort_on_error=1"
    environment["UBSAN_OPTIONS"] = "halt_on_error=1"
    completed = subprocess.run([str(binary)], capture_output=True, text=True,
                               timeout=15, env=environment)
    (folder / (name + ".stdout")).write_text(completed.stdout)
    (folder / (name + ".stderr")).write_text(completed.stderr)
    completed.check_returncode()
    run = {"name": name, "command": command, "tests": [json.loads(line)
           for line in completed.stdout.splitlines()], "stderr": completed.stderr}
    assert len(run["tests"]) == 8
    results["runs"].append(run)
(folder / "test-results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
