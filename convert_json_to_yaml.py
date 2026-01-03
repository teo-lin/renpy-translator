
import json
import yaml
import os
import sys

def convert_json_to_yaml(json_input_path, yaml_output_path):
    try:
        # Read the JSON file content as a string, explicitly handling UTF-8 BOM
        with open(json_input_path, 'r', encoding='utf-8-sig') as f:
            json_string = f.read()

        # Load JSON data from the string
        json_data = json.loads(json_string)

        # Convert JSON to YAML
        # Using default_flow_style=False for a more readable, block-style YAML
        yaml_data = yaml.dump(json_data, default_flow_style=False, sort_keys=False)

        # Write the YAML file
        with open(yaml_output_path, 'w', encoding='utf-8') as f: # Output YAML should still be standard UTF-8
            f.write(yaml_data)

        print(f"Successfully converted '{json_input_path}' to '{yaml_output_path}'")

    except FileNotFoundError:
        print(f"Error: One of the files not found. Check paths: {json_input_path}, {yaml_output_path}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_input_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_json_to_yaml.py <input_json_file> <output_yaml_file>")
        sys.exit(1)

    input_json_file = sys.argv[1]
    output_yaml_file = sys.argv[2]

    convert_json_to_yaml(input_json_file, output_yaml_file)
