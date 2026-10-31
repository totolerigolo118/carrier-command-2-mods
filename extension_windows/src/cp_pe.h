/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * PE header parsing (pure: works on a byte buffer) and the build gate.
 */
#ifndef CP_PE_H
#define CP_PE_H

#include "cp_types.h"

typedef struct cp_pe_info {
    uint16_t machine;          /* 0x014c = i386 */
    uint16_t optional_magic;   /* 0x010b = PE32 */
    uint32_t timestamp;        /* IMAGE_FILE_HEADER.TimeDateStamp */
    uint32_t image_base;       /* preferred base written in the header */
    uint32_t size_of_image;    /* IMAGE_OPTIONAL_HEADER32.SizeOfImage */
} cp_pe_info;

typedef enum cp_pe_status {
    CP_PE_OK = 0,
    CP_PE_TOO_SMALL,
    CP_PE_NO_MZ,
    CP_PE_BAD_LFANEW,
    CP_PE_NO_PE_SIGNATURE,
    CP_PE_NOT_I386,
    CP_PE_NOT_PE32,
    CP_PE_OPTIONAL_TOO_SHORT
} cp_pe_status;

/* Parse the headers at the start of a PE image (file or loaded module). Never reads outside buf. */
cp_pe_status cp_pe_parse(const uint8_t *buf, size_t len, cp_pe_info *out);
const char *cp_pe_status_text(cp_pe_status s);

/* BUILD GATE. Returns 1 only if game_build is CP_KNOWN_BUILD AND the PE timestamp is
 * CP_KNOWN_PE_TIMESTAMP AND SizeOfImage is CP_KNOWN_IMAGE_SIZE. Otherwise returns 0 and writes
 * the reason (first difference found) into reason[cap]. */
int cp_build_gate(const char *game_build, const cp_pe_info *pe, char *reason, size_t cap);

#endif
