/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_config.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "cp_ini.h"

typedef struct ctx {
    cp_config *c;
    cp_tunables *t;
    void (*warn)(void *, const char *);
    void *user;
    int warnings;
} ctx;

#if defined(__GNUC__)
__attribute__((format(printf, 3, 4)))
#endif
static void warn_at(ctx *x, int line, const char *fmt, ...) {
    char msg[200], body[160];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(body, sizeof(body), fmt, ap);
    va_end(ap);
    snprintf(msg, sizeof(msg), "ini line %d: %s", line, body);
    ++x->warnings;
    if (x->warn) x->warn(x->user, msg);
}

static void on_item(void *user, int line, const char *section, const char *key, const char *value) {
    ctx *x = user;
    if (!strcmp(section, "groups")) {
        int g = cp_group_by_key(key), on;
        if (g < 0) { warn_at(x, line, "unknown group '%s'", key); return; }
        if (!cp_parse_bool(value, &on)) {
            x->c->group_on[g] = 0;
            warn_at(x, line, "group '%s': '%s' is not 0/1/on/off (left off)", key, value);
            return;
        }
        x->c->group_on[g] = (uint8_t)on;
    } else if (!strcmp(section, "tunables")) {
        double d;
        if (!cp_parse_double(value, &d)) { warn_at(x, line, "tunable '%s': '%s' is not a number (ignored)", key, value); return; }
        int r = cp_tun_set_by_key(x->t, key, d);
        if (r == 0) warn_at(x, line, "unknown tunable '%s'", key);
        else if (r < 0) warn_at(x, line, "tunable '%s': value '%s' refused (not finite or absurd)", key, value);
        else ++x->c->n_overrides;
    } else if (!strcmp(section, "debug")) {
        int on;
        if (strcmp(key, "lua_speed_stub") != 0) { warn_at(x, line, "unknown debug key '%s'", key); return; }
        if (!cp_parse_bool(value, &on)) { warn_at(x, line, "debug '%s': '%s' is not 0/1 (left off)", key, value); return; }
        x->c->lua_speed_stub = (uint8_t)on;
    } else {
        warn_at(x, line, "key '%s' outside a known section ([groups] [tunables] [debug])", key);
    }
}

static void on_error(void *user, int line, const char *what) {
    ctx *x = user;
    warn_at(x, line, "%s", what);
}

void cp_config_init(cp_config *c) {
    memset(c, 0, sizeof(*c));
}

int cp_config_parse(cp_config *c, cp_tunables *t, const char *buf, size_t len,
                    void (*warn)(void *user, const char *message), void *user) {
    ctx x = { c, t, warn, user, 0 };
    cp_ini_handler h = { on_item, on_error, &x };
    cp_ini_parse(buf, len, &h);
    return x.warnings;
}
