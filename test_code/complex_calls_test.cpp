#include <iostream>
#include <memory>
#include <vector>

namespace TestNamespace {
    class NestedClass {
    public:
        void nestedMethod() { std::cout << "Nested method\n"; }
        static void staticNested() { std::cout << "Static nested\n"; }
    };
}

class ComplexClass {
public:
    void instanceMethod() { std::cout << "Instance method\n"; }
    static void staticMethod() { std::cout << "Static method\n"; }
    
    TestNamespace::NestedClass* getNestedPtr() {
        static TestNamespace::NestedClass instance;
        return &instance;
    }
};

int main() {
    ComplexClass obj;
    ComplexClass* ptr = &obj;
    std::unique_ptr<ComplexClass> smart_ptr = std::make_unique<ComplexClass>();
    std::vector<ComplexClass> vec(3);
    
    // Test all types of function calls in a loop
    for (int i = 0; i < 3; ++i) {
        // Direct object method call
        obj.instanceMethod();
        
        // Pointer method call
        ptr->instanceMethod();
        
        // Smart pointer method call
        smart_ptr->instanceMethod();
        
        // Static method calls
        ComplexClass::staticMethod();
        TestNamespace::NestedClass::staticNested();
        
        // Chained method calls
        ptr->getNestedPtr()->nestedMethod();
        
        // Array/vector access with method call
        vec[i].instanceMethod();
        
        // Namespace qualified direct call
        TestNamespace::NestedClass nested;
        nested.nestedMethod();
    }
    
    return 0;
}