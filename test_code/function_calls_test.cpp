#include <iostream>
#include <vector>
#include <cmath>

class TestClass {
public:
    static void staticMethod(int x) {
        std::cout << "Static method: " << x << std::endl;
    }
    
    void instanceMethod(double y) {
        std::cout << "Instance method: " << y << std::endl;
    }
};

namespace TestNamespace {
    void namespaceFunction(int value) {
        std::cout << "Namespace function: " << value << std::endl;
    }
}

void globalFunction(int a, int b) {
    std::cout << "Global function: " << a << ", " << b << std::endl;
}

int main() {
    TestClass obj;
    std::vector<int> data = {1, 2, 3, 4, 5};
    
    // Loop with various types of function calls
    for (int i = 0; i < 5; ++i) {
        // Global function call
        globalFunction(i, i * 2);
        
        // Static method call with :: notation
        TestClass::staticMethod(i);
        
        // Instance method call
        obj.instanceMethod(std::sqrt(i));
        
        // Namespace function call with :: notation
        TestNamespace::namespaceFunction(i + 10);
        
        // Standard library function calls
        std::cout << "Value: " << std::abs(i - 2) << std::endl;
    }
    
    return 0;
}