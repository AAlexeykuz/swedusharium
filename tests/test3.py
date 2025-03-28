import ast


def parse_transformed_messages(result_str):
    """
    Parses the given result string representing a Python list of strings.

    Parameters:
        result_str (str): A string containing the Python list literal.

    Returns:
        list: A list of transformed message strings.

    Raises:
        ValueError: If the input is not a valid Python list literal.
    """
    try:
        # Safely evaluate the string literal to a Python list
        messages = ast.literal_eval(result_str)
        if not isinstance(messages, list):
            raise ValueError("Parsed object is not a list.")
        # Ensure all elements in the list are strings
        if not all(isinstance(item, str) for item in messages):
            raise ValueError("Not all items in the list are strings.")
        return messages
    except Exception as e:
        raise ValueError(f"Error parsing the result: {e}") from e


# Example usage:
result_str = '["Hello, how are you?", "¡Hola, cómo estás?"]'
try:
    messages = parse_transformed_messages(result_str)
    print("Parsed messages:", messages)
except ValueError as err:
    print("Failed to parse messages:", err)
