import sys

def select_item(title, items, item_formatter_func, item_type_name="item", step_info=""):
    """
    A generic function to prompt the user to select a single item from a list.
    """
    if not items:
        print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    if len(items) == 1:
        item = items[0]
        name = getattr(item, 'name', item.get('name', str(item)))
        print(f"\nAuto-selecting the only available {item_type_name}: {name}")
        return item

    print("\n" + "=" * 70)
    print(f"       {title} {step_info}".strip())
    print("=" * 70 + "\n")

    for i, item in enumerate(items):
        print(item_formatter_func(item, i + 1)) # One item per line for select_item

    print("  [Q] Quit\n")

    while True:
        selection = input(f"Select a {item_type_name} (1-{len(items)} or Q): ")

        if selection.lower() == 'q':
            print("Cancelled by user.")
            sys.exit(0)

        try:
            index = int(selection) - 1
            if 0 <= index < len(items):
                return items[index]
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(items)}.")
        except ValueError:
            print("Invalid input. Please enter a number or Q to quit.")


def select_multiple_items(title, all_items, item_formatter_func, item_type_name="item", step_info=""):
    """
    A generic function to prompt the user to select multiple items from a list,
    displayed one item per line.
    """
    if not all_items:
        print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    print("\n" + "=" * 70)
    print(f"       {title} {step_info}".strip())
    print("=" * 70 + "\n")
    
    # One item per line display
    for i, item in enumerate(all_items):
        print(item_formatter_func(item, i + 1)) # Call formatter and print result
    
    print("\n  [A] Select All")
    print("  [Q] Quit\n")

    while True:
        selection = input(f"Select {item_type_name}s (e.g., 1,3,5 or A or Q): ")

        if selection.lower() == 'q':
            print("Cancelled by user.")
            sys.exit(0)
        
        if selection.lower() == 'a':
            print(f"  Selected: All {len(all_items)} {item_type_name}s")
            return all_items

        try:
            indices = [int(s.strip()) - 1 for s in selection.split(',')]
            selected_indices = sorted(list(set(i for i in indices if 0 <= i < len(all_items))))
            
            if selected_indices:
                selected_items = [all_items[i] for i in selected_indices]
                names = [getattr(item, 'name', item.get('name', str(item))) for item in selected_items]
                print(f"  Selected: {', '.join(names)}")
                return selected_items
            else:
                print("No valid selections made. Please try again.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas, A, or Q.")


def select_languages_single_row(title, all_items, item_formatter_func, item_type_name="language", step_info=""):
    """
    Specific function to prompt the user to select multiple languages,
    displayed in a single long row.
    """
    if not all_items:
        print(f"\nERROR: No {item_type_name}s available to select for '{title}'!")
        raise ValueError(f"No {item_type_name}s to select.")

    print("\n" + "=" * 70)
    print(f"       {title} {step_info}".strip())
    print("=" * 70 + "\n")

    # Display items in a single long row
    formatted_items_strings = []
    for i, item in enumerate(all_items):
        formatted_items_strings.append(item_formatter_func(item, i + 1))
    
    print(" ".join(formatted_items_strings))
    
    print("\n  [A] Select All")
    print("  [Q] Quit\n")

    while True:
        selection = input(f"Select {item_type_name}s (e.g., 1,3,5 or A or Q): ")

        if selection.lower() == 'q':
            print("Cancelled by user.")
            sys.exit(0)
        
        if selection.lower() == 'a':
            print(f"  Selected: All {len(all_items)} {item_type_name}s")
            return all_items

        try:
            indices = [int(s.strip()) - 1 for s in selection.split(',')]
            selected_indices = sorted(list(set(i for i in indices if 0 <= i < len(all_items))))
            
            if selected_indices:
                selected_items = [all_items[i] for i in selected_indices]
                names = [getattr(item, 'name', item.get('name', str(item))) for item in selected_items]
                print(f"  Selected: {', '.join(names)}")
                return selected_items
            else:
                print("No valid selections made. Please try again.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas, A, or Q.")