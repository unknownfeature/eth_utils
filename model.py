import rlp
from eth_hash.auto import keccak


class BasetTxParams:
    """
    Represents the base parameters for an Ethereum transaction, compatible with
    EIP-1559 (London upgrade) transaction types which include gas tip and fee caps.
    """

    def __init__(self, chain_id: int, nonce: int, gas: int, gas_tip_cap: int, gas_fee_cap: int,
                 to=bytes.fromhex('0000000000000000000000000000000000000000'), value=0,
                 data=b''):
        """
        Initializes the base transaction parameters.

        Args:
            chain_id (int): The EIP-155 chain ID of the network (e.g., 1 for Mainnet, 1337 for local dev).
            nonce (int): The transaction count of the sender, used to prevent replay attacks.
            gas (int): The maximum amount of gas the transaction is allowed to consume.
            gas_tip_cap (int): The maximum priority fee (tip) per gas unit the sender is willing to pay to the validator.
            gas_fee_cap (int): The maximum total fee per gas unit the sender is willing to pay (base fee + tip).
            to (bytes): The recipient's address as bytes. Defaults to the zero address (for contract creation).
            value (int): The amount of Ether (in Wei) to send with the transaction. Defaults to 0.
            data (bytes): The arbitrary data payload of the transaction (e.g., contract function call data). Defaults to empty bytes.
        """
        self.chain_id = chain_id
        self.nonce = nonce
        self.gas = gas
        self.gas_tip = gas_tip_cap  # Renamed for consistency with EIP-1559 terminology (maxPriorityFeePerGas)
        self.gas_fee = gas_fee_cap  # Renamed for consistency with EIP-1559 terminology (maxFeePerGas)
        self.to = to
        self.value = value
        self.data = data


class AccessTuple:
    """
    Represents an access tuple as defined in EIP-2930 (Access List transaction type)
    and used in EIP-1559. It specifies an address and a list of storage keys
    that a transaction is expected to access, potentially reducing gas costs.
    """

    def __init__(self, addr: bytes, storage_keys: list[bytes]):
        """
        Initializes an AccessTuple.

        Args:
            addr (bytes): The address of the account being accessed.
            storage_keys (list[bytes]): A list of storage keys (32-byte hashes) within that account being accessed.
        """
        self.storage_keys = storage_keys
        self.addr = addr

    def encode(self) -> list:
        """
        Encodes the AccessTuple into a list suitable for RLP encoding.

        Returns:
            list: A list containing the address and the list of storage keys.
        """
        return [self.addr, self.storage_keys]


class BlobTx:
    """
    Represents an Ethereum EIP-4844 "Blob Transaction" (Type 3 transaction),
    introduced with the Deneb upgrade. These transactions carry large, temporary
    data blobs for scalability improvements, primarily for Layer 2 rollups.
    """

    def __init__(self, tx_params: BasetTxParams, acc_list: list[list],
                 blob_fee_cap: int, blob_hashes: list[bytes]):
        """
        Initializes a BlobTx object.

        Args:
            tx_params (BasetTxParams): The base transaction parameters for the transaction.
            acc_list (list[list]): The access list for the transaction, a list of encoded AccessTuples.
            blob_fee_cap (int): The maximum fee per gas unit for blob data.
            blob_hashes (list[bytes]): A list of Keccak-256 hashes of the commitment to the blobs associated with this transaction.
        """
        self.tx_params = tx_params
        self.acc_list = acc_list
        self.blob_fee_cap = blob_fee_cap
        self.blob_hashes = blob_hashes

    def hash(self) -> bytes:
        """
        Calculates the cryptographic hash of the BlobTx for signing.
        The hash is computed over the RLP-encoded transaction components, prefixed with transaction type '0x03'.

        Returns:
            bytes: The Keccak-256 hash of the transaction.
        """
        # RLP-encodes the transaction components as specified by EIP-4844 for hashing.
        # The '\x03' prefix denotes a Type 3 (Blob) transaction.
        encoded = b'\x03' + rlp.encode(
            [self.tx_params.chain_id, self.tx_params.nonce, self.tx_params.gas_tip, self.tx_params.gas_fee,
             self.tx_params.gas, self.tx_params.to, self.tx_params.value, self.tx_params.data, self.acc_list,
             self.blob_fee_cap, self.blob_hashes])
        return keccak(encoded) # Computes the Keccak-256 hash of the encoded transaction.

    def encode_with_sig(self, v: int, r: bytes, s: bytes) -> bytes:
        """
        Encodes the BlobTx into its raw, signed RLP format, ready for broadcasting to the network.
        Includes the signature components (v, r, s).

        Args:
            v (int): The 'v' component of the transaction signature (recovery ID and chain ID).
            r (bytes): The 'r' component of the transaction signature.
            s (bytes): The 's' component of the transaction signature.

        Returns:
            bytes: The RLP-encoded, signed raw transaction bytes.
        """
        # RLP-encodes the transaction components along with the signature (v, r, s).
        # The '\x03' prefix denotes a Type 3 (Blob) transaction.
        # Note: '\x01' is likely a placeholder or specific encoding related to the signature in this custom context.
        encoded = b'\x03' + rlp.encode(
            [self.tx_params.chain_id, self.tx_params.nonce, self.tx_params.gas_tip, self.tx_params.gas_fee,
             self.tx_params.gas, self.tx_params.to, self.tx_params.value, self.tx_params.data, self.acc_list,
             self.blob_fee_cap, self.blob_hashes, v, r, s]) # v is directly included here, unlike EIP-1559 where it's part of the raw signature
        return encoded


class SetCodeAuthorization:
    """
    Represents a custom authorization structure, likely for an Account Abstraction
    or a specific protocol, allowing an account to set its own code.
    It contains data and a signature that validates this authorization.
    """

    def __init__(self, chain_id: int, addr: bytes, nonce: int, signing_function):
        """
        Initializes a SetCodeAuthorization object. It also signs the authorization upon creation.

        Args:
            chain_id (int): The chain ID for replay protection of the authorization.
            addr (bytes): The address to which this authorization applies (e.g., the account whose code can be set).
            nonce (int): A nonce specific to this authorization, used to prevent replay of the authorization itself.
            signing_function (callable): A function that takes a hash (bytes) and returns a signed message object
                                         (e.g., `web3.eth.account.unsafe_sign_hash`).
        """
        # RLP-encodes the authorization's core data.
        encoded = rlp.encode([chain_id, addr, nonce])
        # Hashes the encoded data, prefixed with '\x05' (likely a custom type identifier for this authorization).
        hashed = keccak(b'\x05' + encoded)
        # Signs the computed hash using the provided signing function.
        signed_msg = signing_function(hashed)
        self.chain_id = chain_id
        self.addr = addr
        self.nonce = nonce
        self.r = signed_msg.r  # The 'r' component of the signature.
        self.s = signed_msg.s  # The 's' component of the signature.
        self.v = signed_msg.v  # The 'v' component of the signature.

    def encode(self) -> list:
        """
        Encodes the SetCodeAuthorization into a list suitable for RLP encoding within a transaction.

        Returns:
            list: A list containing the authorization's data and signature components.
        """
        # Encodes the authorization's components into a list.
        # Note: '\x01' is likely a specific encoding flag or padding for this custom authorization.
        return [self.chain_id, self.addr, self.nonce, '\x01', self.r, self.s]


class SetCodeTx:
    """
    Represents a custom transaction type (likely a Type 4 transaction, given the `\x04` prefix)
    designed to set the code of an Ethereum account, possibly as part of a custom Account Abstraction
    scheme or protocol extension. It includes a list of `SetCodeAuthorization` objects.
    """

    def __init__(self, tx_params: BasetTxParams, acc_list: list[list],
                 set_code_auth_list: list[list]):
        """
        Initializes a SetCodeTx object.

        Args:
            tx_params (BasetTxParams): The base transaction parameters.
            acc_list (list[list]): The access list for the transaction, a list of encoded AccessTuples.
            set_code_auth_list (list[list]): A list of encoded `SetCodeAuthorization` objects required for this transaction.
        """
        self.tx_params = tx_params
        self.acc_list = acc_list
        self.set_code_auth_list = set_code_auth_list

    def hash(self) -> bytes:
        """
        Calculates the cryptographic hash of the SetCodeTx for signing.
        The hash is computed over the RLP-encoded transaction components, prefixed with transaction type '0x04'.

        Returns:
            bytes: The Keccak-256 hash of the transaction.
        """
        # RLP-encodes the transaction components for hashing.
        # The '\x04' prefix denotes a Type 4 (custom SetCode) transaction.
        encoded = b'\x04' + rlp.encode(
            [self.tx_params.chain_id, self.tx_params.nonce, self.tx_params.gas_tip, self.tx_params.gas_fee,
             self.tx_params.gas, self.tx_params.to, self.tx_params.value, self.tx_params.data, self.acc_list,
             self.set_code_auth_list])
        return keccak(encoded) # Computes the Keccak-256 hash.

    def encode_with_sig(self, v: int, r: bytes, s: bytes) -> bytes:
        """
        Encodes the SetCodeTx into its raw, signed RLP format, ready for broadcasting to the network.
        Includes the signature components (v, r, s).

        Args:
            v (int): The 'v' component of the transaction signature.
            r (bytes): The 'r' component of the transaction signature.
            s (bytes): The 's' component of the transaction signature.

        Returns:
            bytes: The RLP-encoded, signed raw transaction bytes.
        """
        # RLP-encodes the transaction components along with the signature (v, r, s).
        # The '\x04' prefix denotes a Type 4 (custom SetCode) transaction.
        return b'\x04' + rlp.encode(
            [self.tx_params.chain_id, self.tx_params.nonce, self.tx_params.gas_tip, self.tx_params.gas_fee,
             self.tx_params.gas, self.tx_params.to, self.tx_params.value, self.tx_params.data, self.acc_list,
             self.set_code_auth_list, v, r, s])