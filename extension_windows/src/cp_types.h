/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * Basic types shared by every file of the CC2 patches plugin.
 *
 * The game is a 32-bit process, so every address handled by the patch code is a 32-bit number
 * (cp_addr). The pure files (patch layer, hook emitter, ini, tunables...) never convert a pointer
 * to a cp_addr: the host-side tests run them over a fake memory with made-up 32-bit addresses.
 */
#ifndef CP_TYPES_H
#define CP_TYPES_H

#include <stddef.h>
#include <stdint.h>

typedef uint32_t cp_addr;

/* Base of the image VAs written in every table (the addresses Ghidra / IDA show). The runtime
 * base can differ (ASLR): the patch layer rebases through env->va(). */
#define CP_IMAGE_BASE 0x00400000u

#if defined(_MSC_VER)
#define CP_ALIGN16 __declspec(align(16))
#else
#define CP_ALIGN16 __attribute__((aligned(16)))
#endif

/* same numbers as CC2X_LOG_* in cc2x.h */
enum { CP_LOG_DEBUG = 0, CP_LOG_INFO = 1, CP_LOG_WARN = 2, CP_LOG_ERROR = 3 };

/* The one game build this plugin accepts (identity only, not a code address). */
#define CP_KNOWN_BUILD "1.5.18-win32"
#define CP_KNOWN_PE_TIMESTAMP 0x6a36c177u
#define CP_KNOWN_IMAGE_SIZE 0x00af7000u

#endif
