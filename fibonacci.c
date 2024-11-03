#include <stdio.h>

void fibonacci(int n) {
    int a = 0, b = 1, next;

    printf("Fibonacci sequence up to %d terms:\n", n);

    for (int i = 1; i <= n; i++) {
        printf("%d ", a);
        next = a + b;
        a = b;
        b = next;
    }
    printf("\n");
}

int main() {
    int n = 10;

    if (n < 1) {
        printf("Please enter a positive integer.\n");
    } else {
        fibonacci(n);
    }

    return 0;
}
