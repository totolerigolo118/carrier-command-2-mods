/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Platform services used by the plugin entry (cc2_patchs.c) and plugged into cp_env.
 * Two implementations: cp_win.c (Win32, the real plugin) and tests/fake_platform.c (a fake
 * address space, for the host-side tests of the whole entry point).
 */
#ifndef CP_PLATFORM_H
#define CP_PLATFORM_H

#include "cp_types.h"

/* Memory: the signatures match cp_env.read / write / alloc_exec. */
int cp_plat_read(void *user, cp_addr a, void *out, uint32_t len);
/* Windows: per page VirtualProtect(PAGE_EXECUTE_READWRITE), copy, restore the protection, then
 * FlushInstructionCache. */
int cp_plat_write(void *user, cp_addr a, const void *data, uint32_t len);
cp_addr cp_plat_alloc_exec(void *user, uint32_t len);

/* Files. read: number of bytes read (at most cap), -1 if the file cannot be opened.
 * write: 1 on success (file created / truncated). */
long cp_plat_read_file(const char *path, void *buf, size_t cap);
int cp_plat_write_file(const char *path, const void *buf, size_t len);

#endif
