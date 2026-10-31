/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Minimal ini parser (pure: works on a memory buffer, no file or Win32 call).
 *
 *   ; comment            # comment
 *   [section]
 *   key = value          ; inline comment (only after a space or tab)
 *
 * Sections and keys are lower-cased; values are trimmed and kept as written. UTF-8 BOM, LF, CR and
 * CRLF line ends are accepted. A later duplicate key simply arrives later (the caller decides).
 */
#ifndef CP_INI_H
#define CP_INI_H

#include <stddef.h>
#include <stdint.h>

#define CP_INI_MAX_LINE 255
#define CP_INI_MAX_NAME 63

typedef struct cp_ini_handler {
    /* one call per "key = value" line; section is "" before the first [section] */
    void (*item)(void *user, int line, const char *section, const char *key, const char *value);
    /* one call per malformed line (the line is skipped) */
    void (*error)(void *user, int line, const char *what);
    void *user;
} cp_ini_handler;

/* Returns the number of malformed lines. */
int cp_ini_parse(const char *buf, size_t len, const cp_ini_handler *h);

/* Locale-independent number parsing of a whole string (leading/trailing blanks allowed). Accepts
 * [+-]digits[.digits][e[+-]digits]. Returns 1 on success. No NaN / inf. */
int cp_parse_double(const char *s, double *out);
/* 1/0, on/off, true/false, yes/no (case-insensitive). Returns 1 on success. */
int cp_parse_bool(const char *s, int *out);

#endif
