#include <stdio.h>

// Simple C example with various loop types
void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int factorial(int n) {
    int result = 1;
    int i = 1;
    
    while (i <= n) {
        result *= i;
        i++;
    }
    
    return result;
}

void print_numbers() {
    int i = 0;
    do {
        printf("%d ", i);
        i++;
    } while (i < 10);
    printf("\n");
}

int main() {
    int numbers[] = {64, 34, 25, 12, 22, 11, 90};
    int n = sizeof(numbers) / sizeof(numbers[0]);
    
    printf("Original array: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", numbers[i]);
    }
    printf("\n");
    
    bubble_sort(numbers, n);
    
    printf("Sorted array: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", numbers[i]);
    }
    printf("\n");
    
    printf("Factorial of 5: %d\n", factorial(5));
    
    print_numbers();
    
    return 0;
}