#!/usr/bin/env python3
"""Compile actual patched IAX functions with a minimal test host and real timerfd."""
import hashlib
import json
import subprocess
from pathlib import Path

folder = Path(__file__).resolve().parent
source = (folder / "chan_iax2.c").read_text()


def function(name):
    marker = "static "
    start = source.rfind(marker, 0, source.index(name + "("))
    end = source.index("\n}\n", source.index(name + "(")) + 3
    return source[start:end]


parts = [function(name) for name in ("update_trunk_timer", "find_tpeer", "iax2_trunk_expired", "timing_read")]
begin = source.index("\t\t\tint previous_trunkfreq;", source.index('!strcasecmp(v->name, "trunkfreq")'))
end = source.index("\t\t\tAST_LIST_UNLOCK(&tpeers);", begin) + len("\t\t\tAST_LIST_UNLOCK(&tpeers);")
reload_body = source[begin:end].replace("atoi(v->value)", "value")
parts.append("static void apply_trunkfreq(int value)\n{\n" + reload_body + "\n}\n")
combined = (folder / "harness-prefix.c").read_text() + "\n".join(parts) + (folder / "harness-tests.c").read_text()
(folder / "harness-generated.c").write_text(combined)
results = {"patched_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
           "extracted_functions": ["update_trunk_timer", "find_tpeer", "iax2_trunk_expired", "timing_read"],
           "reload_test": "Exact patched trunkfreq block, only v->value replaced by test integer"}
for variant, flags in [("normal", ["-O2"]), ("sanitized", ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"])]:
    command = ["cc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-pthread", *flags,
               str(folder / "harness-generated.c"), "-o", str(folder / ("harness-" + variant))]
    compile_result = subprocess.run(command, capture_output=True, text=True)
    record = {"compile_command": command, "compile_exit": compile_result.returncode,
              "compile_stderr": compile_result.stderr}
    if compile_result.returncode == 0:
        run = subprocess.run([str(folder / ("harness-" + variant))], capture_output=True, text=True, timeout=20)
        record.update({"run_exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
    results[variant] = record
(folder / "test-results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
if any(results[v].get("run_exit", 1) for v in ("normal", "sanitized")):
    raise SystemExit(1)
