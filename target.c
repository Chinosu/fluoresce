#include <stdio.h>
#include <stdlib.h>

unsigned long memorize[75];

unsigned long Tribonacci(int n)
{
    if(memorize[n] > 0) return memorize[n];
    else if(n == 0) return memorize[n] = 0;
    else if(n < 3) return memorize[n] = 1;
    else return memorize[n] = (Tribonacci(n - 1) + Tribonacci(n - 2) + Tribonacci(n - 3) );
}

int main()
{
    // int n;
    // while(1)
    // {
    //     printf("Insert the Tribonacci you want to calculate");
    //     scanf("%d", &n);
    //     printf("%lld\n", Tribonacci(n) );
    // }
    // return 0;

    int n = 5;
    printf("%lld\n", Tribonacci(n) );
    return 0;
}