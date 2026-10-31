# Rapport de compilation du plugin `cc2x_hold.dll` — genere par `construire_hold.py`

SDK : clone `7ab05c7` (seul `include/cc2x.h` est utilise, empreinte figee). Compilateur : Zig 0.15.2. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2`. **Rien n'a ete charge, lance dans le jeu, ni copie dans le jeu ou %APPDATA%.**

- taille 223744 octets, sha256 `4837B1B9FC26C3AA236A28564785BF6F74F2BC97D4C3150B54355AD90D89DF17`
- deuxieme compilation identique (hors horodatage PE et identifiant de build) : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; exports : cc2x_plugin_load
- chaines suspectes : aucune
- test hors jeu (UBSan, -Werror) : tous les controles passent
- imports compares a la v1 (`EE9043DA…`) : identiques
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-string-l1-1-0.dll | strlen, strncmp |
| KERNEL32.dll | DeleteCriticalSection, EnterCriticalSection, GetLastError, InitializeCriticalSection, LeaveCriticalSection, Sleep, TlsGetValue, VirtualProtect, VirtualQuery |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, fwrite |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |
