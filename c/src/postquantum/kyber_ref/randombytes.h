#ifndef RANDOMBYTES_H
#define RANDOMBYTES_H

#include <stdint.h>

/**
 * Fill buffer with random bytes from a secure random number generator
 */
void randombytes(uint8_t *out, size_t outlen);

#endif
