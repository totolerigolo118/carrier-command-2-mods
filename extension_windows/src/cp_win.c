/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Win32 implementation of cp_platform.h. This is the only file of the patch layer that calls
 * Windows. It runs inside the loader lock (cc2x_plugin_load is called from DllMain of the SDK):
 * only kernel32 memory and file functions are used, no thread, no wait, no LoadLibrary.
 */
#include <windows.h>
#include <string.h>

#include "cp_platform.h"

#define READABLE (PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ | \
                  PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY)

int cp_plat_read(void *user, cp_addr a, void *out, uint32_t len) {
    (void)user;
    uintptr_t p = (uintptr_t)a;
    uint8_t *dst = out;
    while (len) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery((void *)p, &mbi, sizeof(mbi)) || mbi.State != MEM_COMMIT ||
            !(mbi.Protect & READABLE) || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)))
            return 0;
        uintptr_t end = (uintptr_t)mbi.BaseAddress + mbi.RegionSize;
        uint32_t chunk = (uint32_t)(end - p);
        if (chunk > len) chunk = len;
        memcpy(dst, (const void *)p, chunk);
        dst += chunk;
        p += chunk;
        len -= chunk;
    }
    return 1;
}

int cp_plat_write(void *user, cp_addr a, const void *data, uint32_t len) {
    (void)user;
    uintptr_t p = (uintptr_t)a;
    const uint8_t *src = data;
    while (len) {
        uintptr_t page_end = (p | 0xfffu) + 1;
        uint32_t chunk = (uint32_t)(page_end - p);
        if (chunk > len) chunk = len;
        DWORD old, tmp;
        if (!VirtualProtect((void *)p, chunk, PAGE_EXECUTE_READWRITE, &old)) return 0;
        memcpy((void *)p, src, chunk);
        VirtualProtect((void *)p, chunk, old, &tmp);
        FlushInstructionCache(GetCurrentProcess(), (void *)p, chunk);
        src += chunk;
        p += chunk;
        len -= chunk;
    }
    return 1;
}

cp_addr cp_plat_alloc_exec(void *user, uint32_t len) {
    (void)user;
    static uint8_t *cur, *end;
    len = (len + 15u) & ~15u;
    if (!cur || cur + len > end) {
        cur = VirtualAlloc(NULL, 0x10000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        if (!cur) return 0;
        end = cur + 0x10000;
    }
    uint8_t *r = cur;
    cur += len;
    return (cp_addr)(uintptr_t)r;
}

long cp_plat_read_file(const char *path, void *buf, size_t cap) {
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
                           FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return -1;
    DWORD got = 0;
    BOOL ok = ReadFile(f, buf, (DWORD)cap, &got, NULL);
    CloseHandle(f);
    return ok ? (long)got : -1;
}

int cp_plat_write_file(const char *path, const void *buf, size_t len) {
    HANDLE f = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return 0;
    DWORD put = 0;
    BOOL ok = WriteFile(f, buf, (DWORD)len, &put, NULL);
    CloseHandle(f);
    return ok && put == len;
}
