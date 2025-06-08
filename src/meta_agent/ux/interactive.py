"""Interactive prompt utilities for user input and menus."""

from __future__ import annotations

from typing import Sequence


class Interactive:
    """Handle user prompts and interactive menus."""

    def ask(self, prompt: str) -> str:
        """Return a response to the given prompt."""
        return input(f"{prompt.strip()} ")

    def menu(self, prompt: str, options: Sequence[str]) -> str:
        """Display a numbered menu and return the selected option."""
        if not options:
            raise ValueError("options must not be empty")

        while True:
            print(prompt)
            for idx, opt in enumerate(options, 1):
                print(f"{idx}. {opt}")
            choice = self.ask("Choose an option:")
            if choice.isdigit():
                selected = int(choice) - 1
                if 0 <= selected < len(options):
                    return options[selected]
            print("Invalid choice, try again.")

    def form(self, fields: Sequence[str]) -> dict[str, str]:
        """Prompt for multiple fields and return a mapping of answers."""
        responses: dict[str, str] = {}
        for field in fields:
            responses[field] = self.ask(f"{field}:")
        return responses
