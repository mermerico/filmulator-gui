#ifndef DEBUG_UTILS_H
#define DEBUG_UTILS_H

#include <cmath>
#include <iostream>

#ifdef ENABLE_NAN_TRAPPING
#ifdef __APPLE__
#include <TargetConditionals.h>
#if TARGET_OS_MAC
#include <signal.h>
#define BREAK_ON_NAN(v)                                    \
  if (std::isnan(v)) {                                     \
    std::cerr << "NaN detected! Breaking..." << std::endl; \
    __builtin_debugtrap();                                 \
  }
#else
#define BREAK_ON_NAN(v)                                    \
  if (std::isnan(v)) {                                     \
    std::cerr << "NaN detected! Aborting..." << std::endl; \
    abort();                                               \
  }
#endif
#elif defined(_WIN32)
#include <intrin.h>
#define BREAK_ON_NAN(v)                                    \
  if (std::isnan(v)) {                                     \
    std::cerr << "NaN detected! Breaking..." << std::endl; \
    __debugbreak();                                        \
  }
#else
#include <signal.h>
#define BREAK_ON_NAN(v)                                    \
  if (std::isnan(v)) {                                     \
    std::cerr << "NaN detected! Aborting..." << std::endl; \
    abort();                                               \
  }
#endif

#define SCAN_MATRIX_FOR_NAN(m, name)                                                     \
  do {                                                                                   \
    const float *data = static_cast<const float *>(m);                                   \
    if (data) {                                                                          \
      size_t total = static_cast<size_t>((m).nr()) * (m).nc();                           \
      for (size_t i = 0; i < total; ++i) {                                               \
        if (std::isnan(data[i])) {                                                       \
          std::cerr << "NaN found in matrix " << name << " at index " << i << std::endl; \
          BREAK_ON_NAN(data[i]);                                                         \
          break;                                                                         \
        }                                                                                \
      }                                                                                  \
    }                                                                                    \
  } while (0)
#else
#define BREAK_ON_NAN(v) ((void)0)
#define SCAN_MATRIX_FOR_NAN(m, name) ((void)0)
#endif

#endif// DEBUG_UTILS_H
