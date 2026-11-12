#define _GNU_SOURCE
#include <dlfcn.h>

void *dlopen(const char *file, int mode) {
    static void *(*real)(const char *, int);
    if (!real) real = (void *(*)(const char *, int))dlsym(RTLD_NEXT, "dlopen");
    return real(file, (mode & ~RTLD_NOW) | RTLD_LAZY);
}
