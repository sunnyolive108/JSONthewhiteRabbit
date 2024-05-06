import json
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to input and output files
input_file = os.path.join(script_dir, "input", "input.json")
output_file = os.path.join(script_dir, "output", "output.json")

# Function to extract required key-value pairs and write them to output
def process_json(input_file, output_file):
    result = []

    with open(input_file, "r") as f:
        data = f.read()

    # Split the data into individual JSON objects
    json_objects = data.strip().split('}\n{')

    for obj in json_objects:
        # Reconstruct the JSON object
        obj = obj.strip()
        if not obj.startswith('{'):
            obj = '{' + obj
        if not obj.endswith('}'):
            obj = obj + '}'

        # Load JSON object
        try:
            json_data = json.loads(obj)
        except json.JSONDecodeError:
            print("Error decoding JSON:", obj)
            continue

        # Extract required key-value pairs
        IdOrderWmsHead = json_data.get("IdOrderWmsHead", "")
        HandlingUnitBarcode = json_data.get("HandlingUnitBarcode", "")

        # Print key-value pairs to terminal
        print("IdOrderWmsHead:", IdOrderWmsHead)
        print("HandlingUnitBarcode:", HandlingUnitBarcode)

        # Append key-value pairs to result list
        result.append({
            "IdOrderWmsHead": IdOrderWmsHead,
            "HandlingUnitBarcode": HandlingUnitBarcode
        })

    # Write result to output JSON file
    with open(output_file, "w") as f:
        json.dump(result, f, indent=4)

# Process the JSON file
process_json(input_file, output_file)
