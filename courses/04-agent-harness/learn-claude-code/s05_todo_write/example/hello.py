"""hello.py - A simple greeting module.

This module provides functions for generating personalized greetings.
It can be imported as a module or run directly as a script.
"""


def greet(name: str) -> str:
    """Generate a greeting message for the given name.

    Args:
        name: The name of the person to greet.

    Returns:
        A formatted greeting string.

    Examples:
        >>> greet("World")
        'Hello, World!'
    """
    return f"Hello, {name}!"


def greet_many(names: list[str]) -> list[str]:
    """Generate greeting messages for a list of names.

    Args:
        names: A list of names to greet.

    Returns:
        A list of greeting strings, one for each input name.

    Examples:
        >>> greet_many(["Alice", "Bob"])
        ['Hello, Alice!', 'Hello, Bob!']
    """
    return [greet(name) for name in names]


def main() -> None:
    """Entry point for the hello script.

    Prints a greeting to the console when the module is executed directly.
    """
    print(greet("Claude"))


if __name__ == "__main__":
    main()
