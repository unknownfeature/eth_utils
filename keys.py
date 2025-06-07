from web3 import Web3
# --- Module-level Constants ---
CHAIN_ID_OFFSET = 35 # A constant used in calculating the 'v' component of an Ethereum signature for EIP-155 (replay protection).
V_OFFSET = 27 # A constant used in calculating the 'v' component of an Ethereum signature for pre-EIP-155 transactions.

class Keys:
    """
    A utility class to manage Ethereum account addresses and private keys.
    It provides methods to load keys from various sources and format them correctly.
    """

    def __init__(self, addr, priv_key):
        """
        Initializes a Keys object with an Ethereum address and its corresponding private key.

        Args:
            addr (str): The Ethereum address (e.g., '0x...').
            priv_key (str): The hexadecimal private key string (e.g., '0x...').
        """
        # Converts the provided address to a checksummed address, which is the standard
        # and recommended format for Ethereum addresses to prevent typos.
        self.address = Web3.to_checksum_address(addr)
        self.priv_key = priv_key # Stores the private key as a hexadecimal string.
        # Converts the private key from a hexadecimal string (removing the '0x' prefix) to bytes.
        # This byte representation is often required for signing operations.
        self.priv_key_bytes = bytes.fromhex(priv_key[2:])

    @staticmethod
    def from_geth_file(file_name: str, pswd: str = '') -> callable:
        """
        A static factory method to create a callable that, when executed with a Web3 instance,
        will load keys from a Geth-style keystore file.

        This approach (returning a lambda) allows deferred key loading, which is useful
        when the Web3 instance isn't available at the time the `Keys` object is first configured.

        Args:
            file_name (str): The full path to the Geth keystore file.
            pswd (str, optional): The password for the keystore file. Defaults to an empty string.

        Returns:
            callable: A lambda function that takes a Web3 instance (`w3`) and returns a `Keys` object.
        """
        # Returns a lambda function. When this lambda is called with a Web3 instance (`w3`),
        # it will then call the private `__get_keys_from_file` method.
        # It passes `w3.eth.account.decrypt` as the decryption function, along with the file details.
        return lambda w3: Keys.__get_keys_from_file(w3.eth.account.decrypt, file_name, pswd)

    @staticmethod
    def from_address_and_private_key(address: str, priv_key: str) -> callable:
        """
        A static factory method to create a callable that directly provides keys
        from a given address and private key strings.

        Similar to `from_geth_file`, it returns a lambda for deferred key loading.

        Args:
            address (str): The Ethereum address string.
            priv_key (str): The private key string.

        Returns:
            callable: A lambda function that takes a dummy argument (since `w3` isn't needed here)
                      and returns a `Keys` object.
        """
        # Returns a lambda that directly instantiates a `Keys` object with the provided address and private key.
        # The `_` as a parameter indicates that the lambda accepts an argument but doesn't use it (e.g., a `w3` instance).
        return lambda _: Keys(address, priv_key)

    @staticmethod
    def __get_keys_from_file(decrypt, file_name: str, pswd: str = '') -> 'Keys':
        """
        Private static method to handle the actual decryption and loading of keys from a Geth keystore file.
        This method is typically called by the factory methods (e.g., `from_geth_file`).

        Args:
            decrypt (callable): A decryption function (e.g., `w3.eth.account.decrypt`).
            file_name (str): The path to the keystore file.
            pswd (str, optional): The password for the keystore file. Defaults to an empty string.

        Returns:
            Keys: A `Keys` object containing the loaded address and private key.
        """
        # Extracts the address from the end of the filename. Geth keystore filenames
        # typically end with the address (without '0x').
        addr = file_name[-40:]
        with open(file_name) as keyfile:
            encrypted_key = keyfile.read() # Reads the encrypted key content from the file.
            # Decrypts the encrypted key using the provided decryption function and password.
            private_key = decrypt(encrypted_key, pswd)
            # Returns a new `Keys` object, reconstructing the address with '0x' prefix
            # and converting the decrypted private key bytes back to a hex string with '0x' prefix.
            return Keys('0x' + addr, '0x' + bytes.hex(private_key))


def to_eth_v(v_raw: int, chain_id: int = None) -> int:
    """
    Adjusts the 'v' component of an Ethereum signature based on the chain ID.
    This is crucial for EIP-155 replay protection.

    Ethereum signatures have three components: r, s, and v. The 'v' component
    indicates the parity of the y-coordinate of the public key and, more importantly
    for modern Ethereum, incorporates the chain ID to prevent transactions from being
    valid on different networks (replay attacks).

    Args:
        v_raw (int): The raw 'v' value returned by the signing algorithm (typically 0 or 1).
        chain_id (int, optional): The ID of the Ethereum chain (e.g., 1 for Mainnet, 1337 for local dev).
                                  If None, it assumes a pre-EIP-155 transaction (where `v` is 27 or 28).

    Returns:
        int: The adjusted 'v' value suitable for Ethereum transaction broadcasting.
    """
    if chain_id is None:
        # For pre-EIP-155 transactions, the 'v' value is typically 27 or 28.
        # This adjusts raw v (0 or 1) to the standard 27 or 28.
        v = v_raw - V_OFFSET
    else:
        # For EIP-155 transactions, the 'v' value incorporates the chain ID.
        # The formula is: v = CHAIN_ID * 2 + 35 + raw_v
        # Here, `CHAIN_ID_OFFSET` is 35.
        v = v_raw + CHAIN_ID_OFFSET + 2 * chain_id
    return v