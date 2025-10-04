// Simple C++ example without complex headers
int simple_function() {
    int sum = 0;
    
    // Simple for loop
    for (int i = 0; i < 10; i++) {
        sum += i;
    }
    
    // While loop
    int j = 0;
    while (j < 5) {
        sum += j * 2;
        j++;
    }
    
    return sum;
}

// Nested loops
void nested_loops() {
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            int temp = i * j;
        }
    }
}

int main() {
    int result = simple_function();
    nested_loops();
    return 0;
}