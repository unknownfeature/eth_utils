from eth_hash.auto import keccak

def get_type_def_from_encode(abi_json, filter_func, mapper_func):
  """
  Extracts and flattens a type definition from an ABI JSON, typically used for
  encoding function inputs or outputs.

  This function combines filtering, mapping, and flattening operations to derive
  a concise string representation of a complex data type defined within an ABI.

  Args:
      abi_json (list or dict): The ABI (Application Binary Interface) in JSON format.
                               This usually contains a list of dictionaries, each
                               representing a function, event, or constructor.
      filter_func (callable): A function that takes an ABI item (dict) and returns
                              True if the item should be considered, False otherwise.
                              Example: `lambda item: item['type'] == 'function' and item['name'] == 'myFunction'`
      mapper_func (callable): A function that takes a filtered ABI item (dict) and
                              returns the relevant part containing the type definition,
                              often a list of input or output components.
                              Example: `lambda item: item['inputs']`

  Returns:
      str: A flattened string representation of the complex type definition.
           For example, a struct `struct MyStruct { uint256 id; string name; }`
           might be flattened to `(uint256,string)`.
  """
  # Filters the abi_json using filter_func, then maps the filtered items
  # using mapper_func, and takes the first result using 'next()'.
  type_def = next(map(mapper_func, filter(filter_func, abi_json)))
  # Flattens the extracted type definition into a string.
  return flatten_type_def(type_def)


def flatten_type_def(item):
  """
  Recursively flattens a complex type definition (like structs) into a
  concise string representation.

  This function traverses the 'components' of a type definition, typically
  found in an ABI, to create a compact string that represents its structure.

  Args:
      item (dict or list): A dictionary representing a type definition
                           (e.g., an input/output parameter or a struct component)
                           or a list of such dictionaries (for multiple parameters).

  Returns:
      str: The flattened string representation of the type.
           - For basic types (e.g., 'uint256', 'address'), it returns the type string directly.
           - For complex types (e.g., structs with 'components'), it returns
             a parenthesized comma-separated list of its flattened components:
             `(type1,type2,(subtype1,subtype2))`
  """
  if 'components' in item:
      # If the item has 'components' (indicating a struct or tuple),
      # recursively flatten each component and join them with commas,
      # enclosed in parentheses.
      return '(' + ','.join(flatten_type_def(x) for x in item['components']) + ')'

  # If it's a basic type, return its 'type' string directly.
  return item['type']


def get_function_selector(function_signature: str) -> bytes:
  """
  Calculates the Ethereum function selector (method ID) for a given function signature.

  The function selector is the first four bytes of the Keccak-256 hash of the
  function's canonical signature (e.g., "myFunction(uint256,string)").
  It's used to identify which function is being called in a smart contract transaction.

  Args:
      function_signature (str): The canonical string representation of the function
                                signature (e.g., "transfer(address,uint256)").

  Returns:
      bytes: The 4-byte function selector.
  """
  # Computes the Keccak-256 hash of the UTF-8 encoded function signature.
  # Slices the result to take only the first 4 bytes, which is the selector.
  return keccak(function_signature.encode())[:4]