/* <dlfcn.h> for building iPhone game modules without Apple's SDK (see
 * padmint/ios_module.py). Written for PadMint from POSIX's dynamic linking interface.
 * The flag and handle values are the ones the iPhone's dyld (in libSystem) reads. */
#ifndef _DLFCN_H_
#define _DLFCN_H_

#include <sys/cdefs.h>

__BEGIN_DECLS

typedef struct dl_info {
    const char *dli_fname; /* path of the image holding the address */
    void *dli_fbase;       /* where that image is loaded */
    const char *dli_sname; /* nearest symbol name */
    void *dli_saddr;       /* that symbol's address */
} Dl_info;

extern int dladdr(const void *, Dl_info *);
extern int dlclose(void *__handle);
extern char *dlerror(void);
extern void *dlopen(const char *__path, int __mode);
extern void *dlsym(void *__handle, const char *__symbol);
extern _Bool dlopen_preflight(const char *__path);

#define RTLD_LAZY       0x1
#define RTLD_NOW        0x2
#define RTLD_LOCAL      0x4
#define RTLD_GLOBAL     0x8
#define RTLD_NOLOAD     0x10
#define RTLD_NODELETE   0x80
#define RTLD_FIRST      0x100

#define RTLD_NEXT       ((void *) -1)
#define RTLD_DEFAULT    ((void *) -2)
#define RTLD_SELF       ((void *) -3)
#define RTLD_MAIN_ONLY  ((void *) -5)

__END_DECLS

#endif /* _DLFCN_H_ */
