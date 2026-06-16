# Import necessary modules
import operator

# Define a dictionary to map operator symbols to their corresponding functions
operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

def calculate(num1, operator, num2):
    """
    Perform a calculation based on the provided operator and numbers.

    Args:
        num1 (float): The first number.
        operator (str): The operator to use (+, -, *, /).
        num2 (float): The second number.

    Returns:
        float: The result of the calculation.
    # Check if the operator is valid
    if operator not in operators:
        raise ValueError("Invalid operator")

    # Perform the calculation
    return operators[operator](num1, num2)

def main():
    # Print a welcome message
    print("Simple Calculator")

    # Get user input
    num1 = float(input("Enter the first number: "))
    operator = input("Enter the operator (+, -, *, /): ")
    num2 = float(input("Enter the second number: "))

    try:
        # Perform the calculation and print the result
        result = calculate(num1, operator, num2)
        print(f"{num1} {operator} {num2} = {result}")
    except ValueError as e:
        # Handle invalid operators
        print(e)
    except ZeroDivisionError:
        # Handle division by zero
        print("Error: Division by zero is not allowed")

if __name__ == "__main__":
    main()
