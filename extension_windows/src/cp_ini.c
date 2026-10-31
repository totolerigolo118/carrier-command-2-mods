/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_ini.h"

#include <string.h>

static int is_blank(char c) { return c == ' ' || c == '\t'; }
static char lower(char c) { return (c >= 'A' && c <= 'Z') ? (char)(c + 32) : c; }

static void trim(char *s) {
    size_t n = strlen(s), a = 0;
    while (n > 0 && is_blank(s[n - 1])) s[--n] = 0;
    while (s[a] && is_blank(s[a])) ++a;
    if (a) memmove(s, s + a, n - a + 1);
}

/* cut an inline comment: ';' or '#' preceded by a blank */
static void cut_comment(char *s) {
    for (size_t i = 1; s[i]; ++i)
        if ((s[i] == ';' || s[i] == '#') && is_blank(s[i - 1])) {
            s[i] = 0;
            break;
        }
}

static void handle_line(char *line, int no, char *section, const cp_ini_handler *h, int *errors) {
    trim(line);
    if (!line[0] || line[0] == ';' || line[0] == '#') return;
    if (line[0] == '[') {
        char *end = strchr(line, ']');
        if (!end) goto bad;
        *end = 0;
        char *name = line + 1;
        trim(name);
        if (!name[0] || strlen(name) > CP_INI_MAX_NAME) goto bad;
        for (char *p = name; *p; ++p) *p = lower(*p);
        strcpy(section, name);
        return;
    }
    char *eq = strchr(line, '=');
    if (!eq) goto bad;
    *eq = 0;
    char *key = line, *value = eq + 1;
    trim(key);
    cut_comment(value);
    trim(value);
    if (!key[0] || strlen(key) > CP_INI_MAX_NAME) goto bad;
    for (char *p = key; *p; ++p) *p = lower(*p);
    if (h->item) h->item(h->user, no, section, key, value);
    return;
bad:
    ++*errors;
    if (h->error) h->error(h->user, no, "malformed line (expected [section] or key = value)");
}

int cp_ini_parse(const char *buf, size_t len, const cp_ini_handler *h) {
    char line[CP_INI_MAX_LINE + 1], section[CP_INI_MAX_NAME + 1] = "";
    size_t n = 0;
    int no = 1, errors = 0, too_long = 0;
    if (!buf || !h) return 0;
    if (len >= 3 && (uint8_t)buf[0] == 0xEF && (uint8_t)buf[1] == 0xBB && (uint8_t)buf[2] == 0xBF) {
        buf += 3;
        len -= 3;
    }
    for (size_t i = 0; i <= len; ++i) {
        char c = i < len ? buf[i] : '\n';
        if (c == '\r' && i + 1 < len && buf[i + 1] == '\n') continue;   /* CRLF: the LF ends the line */
        if (c == '\n' || c == '\r') {
            if (too_long) {
                ++errors;
                if (h->error) h->error(h->user, no, "line too long (skipped)");
            } else if (n > 0 || i < len) {
                line[n] = 0;
                handle_line(line, no, section, h, &errors);
            }
            n = 0;
            too_long = 0;
            ++no;
        } else if (n < CP_INI_MAX_LINE) {
            line[n++] = c;
        } else {
            too_long = 1;
        }
    }
    return errors;
}

int cp_parse_double(const char *s, double *out) {
    if (!s || !out) return 0;
    while (is_blank(*s)) ++s;
    int neg = 0;
    if (*s == '+' || *s == '-') neg = (*s++ == '-');
    uint64_t mant = 0;
    int digits = 0, dropped = 0, frac_digits = 0, seen_dot = 0;
    for (;; ++s) {
        if (*s >= '0' && *s <= '9') {
            ++digits;
            if (mant < 100000000000000000ull) {                 /* up to 18 digits kept exactly */
                mant = mant * 10 + (uint64_t)(*s - '0');
                if (seen_dot) ++frac_digits;
            } else if (!seen_dot) {
                ++dropped;                                       /* integer digit beyond precision */
            }
        } else if (*s == '.' && !seen_dot) {
            seen_dot = 1;
        } else {
            break;
        }
    }
    if (!digits) return 0;
    int exp10 = dropped - frac_digits;
    if (*s == 'e' || *s == 'E') {
        ++s;
        int eneg = 0, ed = 0, e = 0;
        if (*s == '+' || *s == '-') eneg = (*s++ == '-');
        for (; *s >= '0' && *s <= '9'; ++s) {
            ++ed;
            if (e < 10000) e = e * 10 + (*s - '0');
        }
        if (!ed) return 0;
        exp10 += eneg ? -e : e;
    }
    while (is_blank(*s)) ++s;
    if (*s) return 0;
    double v = (double)mant;
    if (v != 0.0) {
        if (exp10 > 308 || exp10 < -330) return 0;
        double p = 1.0, base = 10.0;
        for (int e = exp10 < 0 ? -exp10 : exp10; e; e >>= 1, base *= base)
            if (e & 1) p *= base;
        v = exp10 < 0 ? v / p : v * p;
        if (v > 1.7e308) return 0;
    }
    *out = neg ? -v : v;
    return 1;
}

int cp_parse_bool(const char *s, int *out) {
    static const struct { const char *name; int value; } T[] = {
        { "1", 1 }, { "on", 1 }, { "true", 1 }, { "yes", 1 },
        { "0", 0 }, { "off", 0 }, { "false", 0 }, { "no", 0 },
    };
    char word[8];
    size_t n = 0;
    if (!s || !out) return 0;
    while (is_blank(*s)) ++s;
    while (*s && !is_blank(*s) && n < sizeof(word) - 1) word[n++] = lower(*s++);
    word[n] = 0;
    while (is_blank(*s)) ++s;
    if (*s) return 0;
    for (size_t i = 0; i < sizeof(T) / sizeof(T[0]); ++i)
        if (!strcmp(word, T[i].name)) {
            *out = T[i].value;
            return 1;
        }
    return 0;
}
