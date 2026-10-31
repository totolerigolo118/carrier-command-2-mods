#!/bin/sh
# Linux x86_64 seulement (pas le Mac). Depuis ce dossier : sh build.sh && ./diff
set -e
cd "$(dirname "$0")"
SRC=../../../outil/generateurs/cctv_net.s
# version ELF : retirer le prefixe _ des symboles exportes
{ echo ".set TAILLE, 512"; echo ".set ECHELLE, 0x40800000"; sed -e 's/_cctv_/cctv_/g' "$SRC"; } > cctv_elf.s
gcc -no-pie -O1 -Wl,-z,noexecstack -o diff diff.c harness.s cctv_elf.s
