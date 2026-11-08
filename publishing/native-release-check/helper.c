#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) return 1;
    printf("%ld\n", strtol(argv[1], NULL, 10) + 1);
    return 0;
}
