/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Tiny test harness for the host-side tests (no dependency). */
#ifndef CP_TEST_H
#define CP_TEST_H

#include <stdio.h>
#include <string.h>

static int t_checks, t_failed_checks, t_tests, t_failed_tests;
static int t_checks_in_test, t_failed_in_test;

#define CHECK(cond)                                                                        \
    do {                                                                                   \
        ++t_checks; ++t_checks_in_test;                                                    \
        if (!(cond)) {                                                                     \
            ++t_failed_checks; ++t_failed_in_test;                                         \
            printf("    FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);                     \
        }                                                                                  \
    } while (0)

#define CHECK_EQ(a, b)                                                                     \
    do {                                                                                   \
        long long va_ = (long long)(a), vb_ = (long long)(b);                              \
        ++t_checks; ++t_checks_in_test;                                                    \
        if (va_ != vb_) {                                                                  \
            ++t_failed_checks; ++t_failed_in_test;                                         \
            printf("    FAIL %s:%d: %s == %s (got %lld, want %lld)\n", __FILE__, __LINE__, #a, #b, va_, vb_); \
        }                                                                                  \
    } while (0)

#define CHECK_STR_HAS(hay, needle)                                                         \
    do {                                                                                   \
        ++t_checks; ++t_checks_in_test;                                                    \
        if (!strstr((hay), (needle))) {                                                    \
            ++t_failed_checks; ++t_failed_in_test;                                         \
            printf("    FAIL %s:%d: \"%s\" not found in \"%s\"\n", __FILE__, __LINE__, (needle), (hay)); \
        }                                                                                  \
    } while (0)

#define RUN(fn)                                                                            \
    do {                                                                                   \
        t_checks_in_test = 0; t_failed_in_test = 0;                                        \
        fn();                                                                              \
        ++t_tests;                                                                         \
        if (t_failed_in_test) ++t_failed_tests;                                            \
        printf("%s %-46s (%d checks)\n", t_failed_in_test ? "[FAIL]" : "[ ok ]", #fn, t_checks_in_test); \
    } while (0)

#define TEST_SUMMARY()                                                                     \
    (printf("\n%d tests, %d checks, %d failed check(s)\n%s\n", t_tests, t_checks, t_failed_checks, \
            t_failed_checks ? "RESULT: FAIL" : "RESULT: ALL PASS"),                        \
     t_failed_checks ? 1 : 0)

#endif
