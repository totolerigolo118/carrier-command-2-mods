#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Host-side tests (Linux). Nothing here starts the game.
#   1. unit + entry-point tests over a fake address space (gcc, with AddressSanitizer + UBSan)
#   2. the trampoline bytes disassembled by objdump (shown, not asserted)
#   3. the trampoline EXECUTED in a real 32-bit process (Zig, target x86-linux-musl), if Zig is available
# Usage: tests/run_tests.sh      (CC=clang, ZIG="python3 -m ziglang" can be overridden)
set -u
cd "$(dirname "$0")"
SRC=../src
SDK=../../passation_windows/sdk_public_cc2x
OUT=build
CC=${CC:-gcc}
mkdir -p "$OUT"
status=0

echo "### 1. unit and entry-point tests ($($CC --version | head -1))"
$CC -std=c11 -g -O1 -Wall -Wextra -Wpedantic -Werror -Wno-unused-function -fsanitize=address,undefined \
    -fno-sanitize-recover=undefined -I"$SRC" -I"$SDK" \
    test_all.c fake_platform.c "$SRC"/cc2_patchs.c "$SRC"/cp_config.c "$SRC"/cp_groups.c "$SRC"/cp_hook.c \
    "$SRC"/cp_hooks.c "$SRC"/cp_ini.c "$SRC"/cp_patch.c "$SRC"/cp_pe.c "$SRC"/cp_speed.c "$SRC"/cp_tunables.c \
    -lm -o "$OUT"/test_all || exit 2
"$OUT"/test_all || status=1

echo
echo "### 2. trampoline disassembly (objdump, i386, intel syntax)"
if [ -f "$OUT"/trampoline.bin ] && command -v objdump >/dev/null; then
    objdump -D -b binary -m i386 -M intel "$OUT"/trampoline.bin | sed -n '/<.data>:/,$p'
else
    echo "(objdump not available)"
fi

echo
echo "### 3. trampoline executed in a 32-bit process"
if [ -n "${ZIG:-}" ]; then ZIGCMD=($ZIG); elif command -v zig >/dev/null; then ZIGCMD=(zig); else ZIGCMD=(python3 -m ziglang); fi
if "${ZIGCMD[@]}" version >/dev/null 2>&1; then
    export ZIG_GLOBAL_CACHE_DIR=${ZIG_GLOBAL_CACHE_DIR:-$PWD/$OUT/zigcache}
    "${ZIGCMD[@]}" cc -target x86-linux-musl -O1 -g -msse2 -Wall -Wextra -Werror -I"$SRC" \
        test_hook_exec32.c "$SRC"/cp_hook.c -o "$OUT"/test_hook_exec32 || exit 2
    "$OUT"/test_hook_exec32 || status=1
else
    echo "(no Zig available: this step needs it; install with: pip install ziglang==0.15.2)"
fi

echo
echo "### 4. the same unit tests compiled as a 32-bit program (pointer size 4, -Werror)"
if "${ZIGCMD[@]}" version >/dev/null 2>&1; then
    "${ZIGCMD[@]}" cc -target x86-linux-musl -std=c11 -g -O1 -Wall -Wextra -Wpedantic -Werror -Wno-unused-function \
        -I"$SRC" -I"$SDK" \
        test_all.c fake_platform.c "$SRC"/cc2_patchs.c "$SRC"/cp_config.c "$SRC"/cp_groups.c "$SRC"/cp_hook.c \
        "$SRC"/cp_hooks.c "$SRC"/cp_ini.c "$SRC"/cp_patch.c "$SRC"/cp_pe.c "$SRC"/cp_speed.c "$SRC"/cp_tunables.c \
        -o "$OUT"/test_all32 || exit 2
    file "$OUT"/test_all32 2>/dev/null | sed 's/, with debug_info.*//'
    "$OUT"/test_all32 | tail -3 || status=1
    "$OUT"/test_all32 >/dev/null || status=1
else
    echo "(no Zig available)"
fi

echo
echo "### 5. Lua shim (cc2_vitesse over cc2x.speed.mode) with a real Lua 5.3, optional"
if python3 -c "import lupa" >/dev/null 2>&1; then
    python3 check_lua_shim.py || status=1
else
    echo "(skipped: package lupa not installed; pip install lupa)"
fi
exit $status
