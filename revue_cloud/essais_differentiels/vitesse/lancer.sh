#!/bin/sh
# Linux x86_64 seulement (pas le Mac). Depuis ce dossier : sh lancer.sh
set -e
cd "$(dirname "$0")"
python3 extraire.py
gcc -g -O1 -no-pie -Wl,-z,noexecstack -o harnais harnais.c harnais.S
./harnais
