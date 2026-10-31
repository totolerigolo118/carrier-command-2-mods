/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef FAKE_PLATFORM_H
#define FAKE_PLATFORM_H

#include "fake_mem.h"

/* the memory the cp_plat_* functions work on, and a tiny file store */
extern fake_mem *g_plat_mem;
void fp_reset_files(void);
void fp_set_file(const char *path, const char *data, long len);
const char *fp_get_file(const char *path, long *len);   /* NULL if absent */
int fp_file_writes(void);

#endif
