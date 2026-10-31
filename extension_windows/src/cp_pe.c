/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "cp_pe.h"

#include <stdio.h>
#include <string.h>

static uint16_t rd16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

cp_pe_status cp_pe_parse(const uint8_t *buf, size_t len, cp_pe_info *out) {
    if (!buf || !out) return CP_PE_TOO_SMALL;
    memset(out, 0, sizeof(*out));
    if (len < 0x40) return CP_PE_TOO_SMALL;
    if (buf[0] != 'M' || buf[1] != 'Z') return CP_PE_NO_MZ;
    uint32_t nt = rd32(buf + 0x3c);                        /* e_lfanew */
    if (nt < 0x40 || nt > len || len - nt < 4 + 20) return CP_PE_BAD_LFANEW;
    if (memcmp(buf + nt, "PE\0\0", 4) != 0) return CP_PE_NO_PE_SIGNATURE;
    const uint8_t *fh = buf + nt + 4;                      /* IMAGE_FILE_HEADER, 20 bytes */
    out->machine = rd16(fh);
    out->timestamp = rd32(fh + 4);
    uint16_t opt_size = rd16(fh + 16);
    if (out->machine != 0x014c) return CP_PE_NOT_I386;
    size_t opt = (size_t)nt + 4 + 20;                      /* optional header */
    if (len - opt < 2) return CP_PE_OPTIONAL_TOO_SHORT;
    out->optional_magic = rd16(buf + opt);
    if (out->optional_magic != 0x010b) return CP_PE_NOT_PE32;
    /* ImageBase is at +28 and SizeOfImage at +56 of the PE32 optional header */
    if (opt_size < 60 || len - opt < 60) return CP_PE_OPTIONAL_TOO_SHORT;
    out->image_base = rd32(buf + opt + 28);
    out->size_of_image = rd32(buf + opt + 56);
    return CP_PE_OK;
}

const char *cp_pe_status_text(cp_pe_status s) {
    switch (s) {
    case CP_PE_OK: return "ok";
    case CP_PE_TOO_SMALL: return "header too small";
    case CP_PE_NO_MZ: return "no MZ signature";
    case CP_PE_BAD_LFANEW: return "e_lfanew outside the header";
    case CP_PE_NO_PE_SIGNATURE: return "no PE signature";
    case CP_PE_NOT_I386: return "not an i386 image";
    case CP_PE_NOT_PE32: return "not a 32-bit (PE32) image";
    case CP_PE_OPTIONAL_TOO_SHORT: return "optional header too short";
    }
    return "unknown";
}

int cp_build_gate(const char *game_build, const cp_pe_info *pe, char *reason, size_t cap) {
    if (!reason || cap == 0) return 0;
    reason[0] = 0;
    if (!pe) {
        snprintf(reason, cap, "no PE information");
        return 0;
    }
    if (!game_build || strcmp(game_build, CP_KNOWN_BUILD) != 0) {
        snprintf(reason, cap, "game build is '%s', this plugin only knows '%s'",
                 game_build ? game_build : "(null)", CP_KNOWN_BUILD);
        return 0;
    }
    if (pe->timestamp != CP_KNOWN_PE_TIMESTAMP) {
        snprintf(reason, cap, "PE timestamp is 0x%08x, expected 0x%08x", (unsigned)pe->timestamp,
                 (unsigned)CP_KNOWN_PE_TIMESTAMP);
        return 0;
    }
    if (pe->size_of_image != CP_KNOWN_IMAGE_SIZE) {
        snprintf(reason, cap, "SizeOfImage is 0x%08x, expected 0x%08x", (unsigned)pe->size_of_image,
                 (unsigned)CP_KNOWN_IMAGE_SIZE);
        return 0;
    }
    return 1;
}
