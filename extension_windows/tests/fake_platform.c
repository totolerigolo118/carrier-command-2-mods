/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host-side implementation of cp_platform.h over the fake address space. */
#include <string.h>

#include "cp_platform.h"
#include "fake_platform.h"

fake_mem *g_plat_mem;

typedef struct ffile {
    char path[320];
    char data[16384];
    long len;
    int used;
} ffile;
static ffile files[8];
static int file_writes;

void fp_reset_files(void) {
    memset(files, 0, sizeof(files));
    file_writes = 0;
}
void fp_set_file(const char *path, const char *data, long len) {
    for (int i = 0; i < 8; ++i)
        if (!files[i].used || !strcmp(files[i].path, path)) {
            snprintf(files[i].path, sizeof(files[i].path), "%s", path);
            memcpy(files[i].data, data, (size_t)len);
            files[i].len = len;
            files[i].used = 1;
            return;
        }
}
const char *fp_get_file(const char *path, long *len) {
    for (int i = 0; i < 8; ++i)
        if (files[i].used && !strcmp(files[i].path, path)) {
            if (len) *len = files[i].len;
            return files[i].data;
        }
    return NULL;
}
int fp_file_writes(void) { return file_writes; }

int cp_plat_read(void *user, cp_addr a, void *out, uint32_t len) { (void)user; return fm_read(g_plat_mem, a, out, len); }
int cp_plat_write(void *user, cp_addr a, const void *data, uint32_t len) { (void)user; return fm_write(g_plat_mem, a, data, len); }
cp_addr cp_plat_alloc_exec(void *user, uint32_t len) { (void)user; return fm_alloc(g_plat_mem, len); }

long cp_plat_read_file(const char *path, void *buf, size_t cap) {
    long n;
    const char *d = fp_get_file(path, &n);
    if (!d) return -1;
    if ((size_t)n > cap) n = (long)cap;
    memcpy(buf, d, (size_t)n);
    return n;
}
int cp_plat_write_file(const char *path, const void *buf, size_t len) {
    ++file_writes;
    fp_set_file(path, buf, (long)len);
    return 1;
}
