#include <iostream>
#include <memory>

class TestClass {
public:
    void pointerMethod(int x) {
        std::cout << "Pointer method: " << x << std::endl;
    }
    
    static void staticMethod(int y) {
        std::cout << "Static method: " << y << std::endl;
    }
};

struct DataStruct {
    int value;
    void processData() {
        std::cout << "Processing data: " << value << std::endl;
    }
};

int main() {
    // Test pointer-based function calls
    TestClass* ptr = new TestClass();
    std::unique_ptr<DataStruct> smart_ptr = std::make_unique<DataStruct>();
    smart_ptr->value = 42;
    
    // Loop with pointer-based method calls
    for (int i = 0; i < 3; ++i) {
        // Direct pointer method call
        ptr->pointerMethod(i);
        
        // Smart pointer method call
        smart_ptr->processData();
        
        // Static method call (should still work)
        TestClass::staticMethod(i * 2);
    }
    
    delete ptr;
    return 0;
}