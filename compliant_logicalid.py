#!/usr/bin/python
import os
import json
import yaml
import re

# Declare global variables for color codes
COLOR_CODES = {
    'compliant': '\033[32m',  # Green
    'error': '\033[31m',      # Red
    'reset': '\033[0m'        # Reset to default
}

class CloudFormationValidator:
    def __init__(self, directory, exclusion_file):
        self.directory = directory
        self.exclusion_file = exclusion_file
        self.EXCLUSION_LIST = []  # Initialize the exclusion list as an instance attribute
        self.load_exclusion_list()

    def clean_string(self, string):
        """Remove unwanted characters like escape sequences and control characters."""
        return re.sub(r'\x1b[^m]*m', '', string).strip()  # This removes any ANSI escape codes

    def load_exclusion_list(self):
        """Load exclusion list from the provided file into the instance attribute."""
        try:
            with open(self.exclusion_file, 'r') as f:
                # Read lines, clean each line by removing control characters and extra spaces
                self.EXCLUSION_LIST = [
                    self.clean_string(line) for line in f.readlines() if line.strip()
                ]
                #print(f"Exclusion List Loaded: {self.EXCLUSION_LIST}")
                #print(len(self.EXCLUSION_LIST))
        except FileNotFoundError:
            print(f"Exclusion file {self.exclusion_file} not found!")

    def validate_logical_ids_in_file(self, file):
        """Validate that logical IDs in the file follow the correct format."""
        try:
            with open(file, 'r') as f:
                data = json.load(f) if file.endswith('.json') else yaml.safe_load(f)

            for logical_id, resource in data.get("Resources", {}).items():
                # Clean the logical ID to avoid any control characters or escape sequences
                cleaned_logical_id = self.clean_string(logical_id)

                # Skip the resource if its cleaned logical ID is in the exclusion list
                if cleaned_logical_id in self.EXCLUSION_LIST:
               #     print(f"{COLOR_CODES['error']}Skipping Logical ID: {cleaned_logical_id}{COLOR_CODES['reset']}")
                    print(cleaned_logical_id)
                    continue  # Skip this resource if its logical ID is in the exclusion list

                # The logical ID is the key of the resource in the "Resources" section
                resource_type = resource.get('Type', '')
                type_parts = resource_type.split("::")
                if len(type_parts) > 1:
                    # Simplified, using the last two parts directly
                    expected_logical_id_end = ''.join(type_parts[-2:])
                    if not cleaned_logical_id.lower().endswith(expected_logical_id_end.lower()):
                        print(cleaned_logical_id.lower())
                        print(expected_logical_id_end.lower())
                        print(f"{COLOR_CODES['error']}Error: Logical ID '{cleaned_logical_id}' for resource '{resource_type}' in '{f}' is not compliant with the expected format.{COLOR_CODES['reset']}")
                        return
                else:
                    print(f"{COLOR_CODES['error']}Error: Missing or invalid resource type for '{cleaned_logical_id}'.{COLOR_CODES['reset']}")
                    return

            # If we reach here, it means the file is compliant
            print(f"{COLOR_CODES['compliant']}Compliant: {file}{COLOR_CODES['reset']}")

        except json.JSONDecodeError:
            print(f"{COLOR_CODES['error']}Error: Failed to parse JSON file: {file}{COLOR_CODES['reset']}")
        except yaml.YAMLError:
            print(f"{COLOR_CODES['error']}Error: Failed to parse YAML file: {file}{COLOR_CODES['reset']}")
        except Exception as e:
            print(f"{COLOR_CODES['error']}Error: {e}{COLOR_CODES['reset']}")

    def validate_all_files(self):
        """Validate all JSON and YAML files in the given directory and subdirectories."""
        files = []
        excluded_files = ["clusters.json", "bamboo.yml", "dev.manifest.json", "prod.manifest.json"]  # List of files to exclude
        for root, _, filenames in os.walk(self.directory):
            for filename in filenames:
                if filename.endswith(('.json', '.yaml', '.yml')):
                    full_path = os.path.join(root, filename)
                    # Skip "clusters.json" files and other files in exclusion list
                    if any(excluded_file in full_path for excluded_file in excluded_files):
                        print(f"{COLOR_CODES['error']}Skipping {filename} file: {full_path}{COLOR_CODES['reset']}")
                        continue
                    files.append(full_path)

        for file in files:
            self.validate_logical_ids_in_file(file)


if __name__ == "__main__":
    directory_to_check = '.'  # Replace with your directory
    exclusion_file = './exclusion_list.txt'  # Replace with your exclusion list file path
    validator = CloudFormationValidator(directory_to_check, exclusion_file)
    validator.validate_all_files()
