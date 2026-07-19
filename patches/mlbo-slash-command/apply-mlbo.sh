#!/usr/bin/env bash
# apply-mlbo.sh — /mlbo 슬래시 커맨드 로컬 엔진 패치 재적용기.
#
# GJC 0.10.x~0.11.x 는 사용자 확장/커맨드 표면이 격리(quarantine)돼 있어
# 커스텀 슬래시 커맨드는 builtin-registry.ts 직접 패치로만 가능하다.
# `gjc update` 가 패키지를 덮어쓰면 이 스크립트를 다시 실행하라.
#
# 사용: apply-mlbo.sh [block-file]   (기본: 이 스크립트 옆의 mlbo-block.ts)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCK="${1:-$HERE/mlbo-block.ts}"
[ -f "$BLOCK" ] || { echo "block file not found: $BLOCK" >&2; exit 1; }

GJC_BIN="$(readlink -f "$(command -v gjc)")"
REG="$(dirname "$GJC_BIN")/../node_modules/@gajae-code/coding-agent/src/slash-commands/builtin-registry.ts"
[ -f "$REG" ] || REG="$(dirname "$GJC_BIN")/../../@gajae-code/coding-agent/src/slash-commands/builtin-registry.ts"
[ -f "$REG" ] || { echo "builtin-registry.ts not found near $GJC_BIN" >&2; exit 1; }
REG="$(readlink -f "$REG")"

python3 - "$REG" "$BLOCK" <<'PY'
import re, shutil, sys, time
reg, blockfile = sys.argv[1], sys.argv[2]
src = open(reg, encoding="utf-8").read()
block = open(blockfile, encoding="utf-8").read()

# 1) import 보강
if "activateModelProfile," not in src:
    src2 = src.replace(
        'import { materializeActiveModelProfileAssignments } from "../config/model-profile-activation";',
        'import { activateModelProfile, materializeActiveModelProfileAssignments } from "../config/model-profile-activation";',
        1,
    )
    assert src2 != src, "import anchor not found — engine layout changed, patch manually"
    src = src2

# 2) 기존 블록 제거(재실행 대비) 후 /effort 커맨드 앞에 삽입
src = re.sub(r'\t// >>> mlbo-patch.*?\t// <<< mlbo-patch <<<\n', '', src, flags=re.S)
anchor = re.search(r'\t\{\n\t\tname: "effort",', src)
assert anchor, 'anchor `name: "effort"` not found — engine layout changed, patch manually'
backup = f"{reg}.bak-mlbo-{time.strftime('%Y%m%d-%H%M%S')}"
shutil.copyfile(reg, backup)
src = src[: anchor.start()] + block + src[anchor.start():]
open(reg, "w", encoding="utf-8").write(src)
print(f"patched: {reg}\nbackup : {backup}")
PY

echo "OK — 새 gjc 세션부터 /mlbo 사용 가능"
