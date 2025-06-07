import json

def read_contract_json(file_name: str) -> dict:
    """
    Reads and parses a JSON file, typically used for loading smart contract ABI and bytecode.

    Args:
        file_name (str): The path to the JSON file to be read.

    Returns:
        dict: A dictionary representing the parsed JSON content of the file.
              This dictionary commonly contains the contract's ABI, bytecode,
              and other compilation artifacts.
    """
    # Open the specified file in read mode ('r'). The 'with' statement ensures
    # the file is properly closed after its block is exited.
    with open(file_name, 'r') as fle:
        # Load (parse) the JSON content from the file object and return it as a Python dictionary.
        return json.load(fle)