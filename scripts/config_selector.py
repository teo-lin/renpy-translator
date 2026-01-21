import sys

def _safe_print(*args, **kwargs):
    """
    Safe print that handles closed stderr (can happen during pytest).
    Falls back to stdout if stderr is closed.
    """
    if 'file' not in kwargs:
        kwargs['file'] = sys.stderr

    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        # stderr is closed, try stdout
        kwargs['file'] = sys.stdout
        try:
            print(*args, **kwargs)
        except (ValueError, OSError):
            # Both closed, silently ignore
            pass

def select_item(title, items, item_formatter_func, item_type_name="item", step_info=""):
    """
    A generic function to prompt the user to select a single item from a list.
    All output goes to stderr so prompts are visible even when stdout is captured.
    """
    if not items:
        _safe_print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    if len(items) == 1:
        item = items[0]
        name = getattr(item, 'name', item.get('name', str(item)))
        _safe_print(f"\nAuto-selecting the only available {item_type_name}: {name}")
        return item

    _safe_print("\n" + "=" * 70)
    _safe_print(f"       {title} {step_info}".strip())
    _safe_print("=" * 70 + "\n")

    for i, item in enumerate(items):
        _safe_print(item_formatter_func(item, i + 1)) # One item per line for select_item

    _safe_print("  [Q] Quit\n")

    while True:
        # Prompt to stderr, but input() reads from stdin
        _safe_print(f"Select a {item_type_name} (1-{len(items)} or Q): ", end='', flush=True)
        selection = input()

        if selection.lower() == 'q':
            _safe_print("Cancelled by user.")
            sys.exit(0)

        try:
            index = int(selection) - 1
            if 0 <= index < len(items):
                return items[index]
            else:
                _safe_print(f"Invalid selection. Please enter a number between 1 and {len(items)}.")
        except ValueError:
            _safe_print("Invalid input. Please enter a number or Q to quit.")


def select_multiple_items(title, all_items, item_formatter_func, item_type_name="item", step_info=""):
    """
    A generic function to prompt the user to select multiple items from a list,
    displayed one item per line.
    All output goes to stderr so prompts are visible even when stdout is captured.
    """
    if not all_items:
        _safe_print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    _safe_print("\n" + "=" * 70)
    _safe_print(f"       {title} {step_info}".strip())
    _safe_print("=" * 70 + "\n")

    # One item per line display
    for i, item in enumerate(all_items):
        _safe_print(item_formatter_func(item, i + 1)) # Call formatter and print result

    _safe_print("\n  [A] Select All")
    _safe_print("  [Q] Quit\n")

    while True:
        _safe_print(f"Select {item_type_name}s (e.g., 1,3,5 or A or Q): ", end='', flush=True)
        selection = input()

        if selection.lower() == 'q':
            _safe_print("Cancelled by user.")
            sys.exit(0)

        if selection.lower() == 'a':
            _safe_print(f"  Selected: All {len(all_items)} {item_type_name}s")
            return all_items

        try:
            indices = [int(s.strip()) - 1 for s in selection.split(',')]
            selected_indices = sorted(list(set(i for i in indices if 0 <= i < len(all_items))))

            if selected_indices:
                selected_items = [all_items[i] for i in selected_indices]
                names = [getattr(item, 'name', item.get('name', str(item))) for item in selected_items]
                _safe_print(f"  Selected: {', '.join(names)}")
                return selected_items
            else:
                _safe_print("No valid selections made. Please try again.")
        except ValueError:
            _safe_print("Invalid input. Please enter numbers separated by commas, A, or Q.")


def select_languages_single_row(title, all_items, item_formatter_func, item_type_name="language", step_info=""):
    """
    Specific function to prompt the user to select multiple languages,
    displayed in a single long row.
    All output goes to stderr so prompts are visible even when stdout is captured.
    """
    if not all_items:
        _safe_print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    _safe_print("\n" + "=" * 70)
    _safe_print(f"       {title} {step_info}".strip())
    _safe_print("=" * 70 + "\n")

    # Display items in a single long row
    formatted_items_strings = []
    for i, item in enumerate(all_items):
        formatted_items_strings.append(item_formatter_func(item, i + 1))

    _safe_print(" ".join(formatted_items_strings))

    _safe_print("\n  [A] Select All")
    _safe_print("  [Q] Quit\n")

    while True:
        _safe_print(f"Select {item_type_name}s (e.g., 1,3,5 or A or Q): ", end='', flush=True)
        selection = input()

        if selection.lower() == 'q':
            _safe_print("Cancelled by user.")
            sys.exit(0)

        if selection.lower() == 'a':
            _safe_print(f"  Selected: All {len(all_items)} {item_type_name}s")
            return all_items

        try:
            indices = [int(s.strip()) - 1 for s in selection.split(',')]
            selected_indices = sorted(list(set(i for i in indices if 0 <= i < len(all_items))))

            if selected_indices:
                selected_items = [all_items[i] for i in selected_indices]
                names = [getattr(item, 'name', item.get('name', str(item))) for item in selected_items]
                _safe_print(f"  Selected: {', '.join(names)}")
                return selected_items
            else:
                _safe_print("No valid selections made. Please try again.")
        except ValueError:
            _safe_print("Invalid input. Please enter numbers separated by commas, A, or Q.")