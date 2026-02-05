# -*- coding: utf-8 -*-
"""
Legacy Calculator Module - Python 2 Style

This module demonstrates various Python 2 patterns that need migration.
"""

def add(a, b):
    """Add two numbers."""
    print "Adding %d + %d" % (a, b)
    return a + b


def subtract(a, b):
    """Subtract two numbers."""
    print "Subtracting %d - %d" % (a, b)
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    print "Multiplying %d * %d" % (a, b)
    return a * b


def divide(a, b):
    """Divide two numbers (integer division in Python 2)."""
    if b == 0:
        print "Error: Division by zero!"
        return None
    print "Dividing %d / %d" % (a, b)
    return a / b  # Integer division in Python 2


def power(base, exp):
    """Calculate power using a loop."""
    result = 1
    for i in xrange(exp):
        result *= base
    print "Result: %d ^ %d = %d" % (base, exp, result)
    return result


def factorial(n):
    """Calculate factorial using xrange."""
    if n < 0:
        print "Error: Negative number!"
        return None
    result = 1
    for i in xrange(1, n + 1):
        result *= i
    print "Factorial of %d is %d" % (n, result)
    return result


def get_user_input():
    """Get calculator input from user."""
    print "=== Python 2 Calculator ==="
    
    num1 = raw_input("Enter first number: ")
    num2 = raw_input("Enter second number: ")
    operation = raw_input("Enter operation (+, -, *, /, ^): ")
    
    try:
        a = int(num1)
        b = int(num2)
    except ValueError, e:
        print "Error: Invalid number - " + str(e)
        return None
    
    if operation == '+':
        return add(a, b)
    elif operation == '-':
        return subtract(a, b)
    elif operation == '*':
        return multiply(a, b)
    elif operation == '/':
        return divide(a, b)
    elif operation == '^':
        return power(a, b)
    else:
        print "Unknown operation: " + operation
        return None


def batch_calculate(operations):
    """Process a batch of operations from a dictionary."""
    results = {}
    
    for key, value in operations.iteritems():
        op = value.get('operation')
        a = value.get('a')
        b = value.get('b')
        
        print "Processing operation: " + key
        
        if op == 'add':
            results[key] = add(a, b)
        elif op == 'subtract':
            results[key] = subtract(a, b)
        elif op == 'multiply':
            results[key] = multiply(a, b)
        elif op == 'divide':
            results[key] = divide(a, b)
    
    return results


if __name__ == "__main__":
    # Test the calculator
    print "Testing Calculator Module"
    print "========================="
    
    result = get_user_input()
    if result is not None:
        print "Final result: " + str(result)
