# Rapport de compilation (etape 3) — genere par `construire.py`

Commit du SDK : `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`. Compilateur : Zig 0.15.2. Dossier de travail (hors depot, hors jeu) : `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail`. Options = celles de `build.py` du SDK. **Rien n'a ete charge ni lance (les deux DLL), rien copie dans le jeu.**

## dinput8.dll

- taille 267264 octets, sha256 `184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982`
- deuxieme compilation identique, hors horodatage PE et identifiant de build (20 octets) : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents; exports : DirectInput8Create, DllCanUnloadNow, DllGetClassObject, DllRegisterServer, DllUnregisterServer
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-math-l1-1-0.dll | atan2 |
| api-ms-win-crt-private-l1-1-0.dll | strrchr, strstr, wcsrchr |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, __stdio_common_vswprintf, fclose, fopen, fwrite |
| api-ms-win-crt-string-l1-1-0.dll | _wcsicmp, strcmp, strlen, strncmp, wcscat, wcscpy, wcslen, wcsncpy |
| api-ms-win-crt-utility-l1-1-0.dll | qsort |
| KERNEL32.dll | CloseHandle, CreateDirectoryW, CreateFileW, DeleteCriticalSection, DeleteFileA, EnterCriticalSection, FindClose, FindFirstFileW, FindNextFileW, FlushInstructionCache, GetCurrentProcess, GetEnvironmentVariableW, GetFileAttributesW, GetFileSize, GetLastError, GetLocalTime, GetModuleFileNameA, GetModuleFileNameW, GetModuleHandleExW, GetModuleHandleW, GetPrivateProfileIntA, GetProcAddress, GetProcessHeap, GetSystemDirectoryW, HeapAlloc, HeapFree, InitOnceExecuteOnce, InitializeCriticalSection, LeaveCriticalSection, LoadLibraryExW, LoadLibraryW, MultiByteToWideChar, ReadFile, Sleep, TlsGetValue, VirtualAlloc, VirtualProtect, VirtualQuery, WideCharToMultiByte |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |

## cc2x_frein.dll

- taille 240640 octets, sha256 `941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3`
- deuxieme compilation identique, hors horodatage PE et identifiant de build (20 octets) : oui
- PE32 i386 DLL : True ; TLS : present, callbacks identiques a ceux d une DLL vide (code du compilateur) ; imports retardes : absents; exports : cc2x_plugin_load
- chaines suspectes : aucune
- verdict automatique : OK

| DLL importee | fonctions |
|---|---|
| api-ms-win-crt-convert-l1-1-0.dll | atof |
| api-ms-win-crt-private-l1-1-0.dll | strchr |
| api-ms-win-crt-runtime-l1-1-0.dll | _execute_onexit_table, _exit, _initialize_onexit_table, _initterm, _initterm_e, _register_onexit_function, abort |
| api-ms-win-crt-string-l1-1-0.dll | strcmp, strlen, strncmp |
| KERNEL32.dll | DeleteCriticalSection, EnterCriticalSection, GetLastError, GetModuleHandleA, GetPrivateProfileStringA, InitializeCriticalSection, LeaveCriticalSection, Sleep, TlsGetValue, VirtualProtect, VirtualQuery |
| api-ms-win-crt-stdio-l1-1-0.dll | __acrt_iob_func, __stdio_common_vfprintf, __stdio_common_vsprintf, fwrite |
| api-ms-win-crt-heap-l1-1-0.dll | calloc, free |
