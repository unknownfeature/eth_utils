from typing import Union
from eth_typing import HexStr
from web3 import Web3


class Client:
    """
    A client class for interacting with an Ethereum blockchain.
    It encapsulates Web3.py functionalities for sending transactions,
    deploying contracts, calling contract functions, and fetching blockchain data.
    """

    def __init__(self, url: str, keys_supplier):
        """
        Initializes the Ethereum client.

        Args:
            url (str): The URL of the Ethereum node (e.g., 'http://localhost:8545', 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID').
            keys_supplier: A callable (function or class) that takes a Web3 instance
                           and returns an object with `address` and `priv_key` attributes.
                           This allows flexible key loading (e.g., from a keystore file, environment variable).
        """
        self.w3 = Web3(Web3.HTTPProvider(url))  # Initializes the Web3.py instance with an HTTP provider.
        self.keys = keys_supplier(self.w3)  # Loads the keys using the provided keys_supplier, passing the Web3 instance.

    def send_transaction(self, transaction: dict, gas: int = 8000000, verbose=True):
        """
        Sends a general Ethereum transaction. This method expects a partially built
        transaction dictionary and will add the nonce and gas before signing and sending.

        Args:
            transaction (dict): A dictionary representing the transaction to be sent (e.g., {'to': '0x...', 'value': ...}).
            gas (int): The maximum gas limit for the transaction. Defaults to 8,000,000.
            verbose (bool): If True, prints raw transaction hex and receipt details. Defaults to True.

        Returns:
            web3.types.TxReceipt: The transaction receipt once the transaction is mined.
        """
        # Get the latest transaction count for the sender's address. 'pending' ensures
        # that even transactions currently in the mempool are accounted for.
        nonce = self.w3.eth.get_transaction_count(self.keys.address, block_identifier='pending')
        transaction['nonce'] = nonce  # Assign the obtained nonce to the transaction.
        transaction['gas'] = gas  # Set the gas limit for the transaction.
        return self.__sign_send_wait(transaction, verbose)  # Sign, send, and wait for the transaction to be mined.

    def __send_and_wait(self, raw_transaction: Union[HexStr, bytes], verbose=True):
        """
        Internal helper method to send a raw, signed transaction and wait for its receipt.

        Args:
            raw_transaction (Union[HexStr, bytes]): The RLP-encoded and signed transaction.
            verbose (bool): If True, prints the raw transaction hex and the receipt. Defaults to True.

        Returns:
            web3.types.TxReceipt: The transaction receipt.
        """
        # Send the raw, signed transaction to the Ethereum node.
        tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
        if verbose:
            # Print the raw transaction in hex format for debugging/logging.
            print(raw_transaction.hex() if isinstance(raw_transaction, bytes) else raw_transaction)
        # Wait for the transaction to be included in a block and get its receipt.
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if verbose:
            print(receipt)  # Print the transaction receipt.
        return receipt

    def __sign_send_wait(self, transaction, verbose):
        """
        Internal helper method to sign a transaction, send it, and wait for its receipt.

        Args:
            transaction (dict): The transaction dictionary to be signed and sent.
            verbose (bool): If True, enables verbose output for sending and waiting.

        Returns:
            web3.types.TxReceipt: The transaction receipt.
        """
        # Sign the transaction using the private key.
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.keys.priv_key)
        # Call the internal helper to send the raw signed transaction and wait.
        return self.__send_and_wait(signed_txn.raw_transaction, verbose)

    def send_signed_raw_transaction(self, raw_tx, verbose=True):
        """
        Sends a pre-signed, raw transaction directly to the network and waits for its receipt.
        This is useful when the transaction has been signed externally.

        Args:
            raw_tx (Union[HexStr, bytes]): The RLP-encoded and signed transaction.
            verbose (bool): If True, enables verbose output for sending and waiting.

        Returns:
            web3.types.TxReceipt: The transaction receipt.
        """
        return self.__send_and_wait(raw_tx, verbose)  # Utilize the internal helper.

    def deploy_contract(self, contract_json, *params, gas: int = 8000000, get_abi=lambda x: x['abi'], value=0,
                        get_bytecode=lambda x: x['bytecode'], verbose=True, ) -> str:
        """
        Deploys a smart contract to the Ethereum blockchain.

        Args:
            contract_json (dict): A dictionary representing the compiled contract JSON (e.g., from Truffle or Hardhat artifacts).
            *params: Arguments to pass to the contract's constructor.
            gas (int): The maximum gas limit for the deployment transaction. Defaults to 8,000,000.
            get_abi (callable): A function that extracts the ABI from `contract_json`. Defaults to `lambda x: x['abi']`.
            value (int): The amount of Ether (in wei) to send with the deployment transaction. Defaults to 0.
            get_bytecode (callable): A function that extracts the bytecode from `contract_json`. Defaults to `lambda x: x['bytecode']`.
            verbose (bool): If True, enables verbose output for signing and sending. Defaults to True.

        Returns:
            str: The address of the deployed contract.
        """
        # Get the current nonce for the sender's account.
        nonce = self.w3.eth.get_transaction_count(self.keys.address, block_identifier='pending')
        # Create a contract object from its ABI and bytecode.
        contract = self.w3.eth.contract(abi=get_abi(contract_json), bytecode=get_bytecode(contract_json))
        # Build the transaction to deploy the contract, passing constructor parameters.
        transaction = contract.constructor(*params).build_transaction(
            {'from': self.keys.address, 'nonce': nonce, 'gas': gas, 'value': value})
        # Sign, send, wait for the receipt, and then return the deployed contract's address.
        return self.__sign_send_wait(transaction, verbose).contractAddress

    def transact_function(self, contract_address, contract_abi, function_name, *params, gas: int = 8000000,
                          value=0,
                          verbose=True, ):
        """
        Sends a transaction to interact with a smart contract function (i.e., a state-changing function).

        Args:
            contract_address (str): The hexadecimal address of the deployed contract.
            contract_abi (list): The ABI (Application Binary Interface) of the contract.
            function_name (str): The name of the function to call on the contract.
            *params: Arguments to pass to the contract function.
            gas (int): The maximum gas limit for the transaction. Defaults to 8,000,000.
            value (int): The amount of Ether (in wei) to send with the transaction. Defaults to 0.
            verbose (bool): If True, prints details about the function call and its status. Defaults to True.

        Returns:
            web3.types.TxReceipt: The transaction receipt once the transaction is mined.
        """
        # Get the current nonce.
        nonce = self.w3.eth.get_transaction_count(self.keys.address, block_identifier='pending')
        # Create a contract instance from its address and ABI.
        contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
        # Build the transaction to call the specified function with its parameters.
        transaction = contract.functions[function_name](*params).build_transaction(
            {"from": self.keys.address, 'nonce': nonce, 'gas': gas, 'value': value})
        # Sign the transaction.
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.keys.priv_key)
        # Send the raw signed transaction.
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        # Wait for the transaction receipt.
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if verbose:
            # Print details about the function call and its success/failure status.
            print(
                f'called {function_name} on {contract_address} with params: {params} and status {receipt.status}\n')
        return receipt

    def call_function(self, contract_address, contract_abi, function_name, *params, verbose=True):
        """
        Calls a read-only (view/pure) function on a smart contract.
        These calls do not create a transaction, do not cost gas, and do not change blockchain state.

        Args:
            contract_address (str): The hexadecimal address of the deployed contract.
            contract_abi (list): The ABI of the contract.
            function_name (str): The name of the function to call.
            *params: Arguments to pass to the contract function.
            verbose (bool): If True, prints the function call details and its result. Defaults to True.

        Returns:
            Any: The result returned by the contract function.
        """
        # Create a contract instance.
        contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
        # Call the specified function with its parameters.
        # `block_identifier='pending'` ensures the call reflects the latest state, including pending transactions.
        res = contract.functions[function_name](*params).call({'to': contract_address},
                                                              block_identifier='pending')
        if verbose:
            # Print the contract address, function name, parameters, and the returned result.
            print(f'{contract_address}.{function_name} {params} = {res}\n')
        return res

    def sign_hash(self, hashed):
        """
        Signs a given hash using the client's private key.
        This is a low-level signing operation.

        Args:
            hashed (bytes): The bytes hash to be signed.

        Returns:
            web3.datastructures.SignedMessage: An object containing the `v`, `r`, and `s` components of the signature.
        """
        # Uses web3.py's `unsafe_sign_hash` as it directly signs a hash, without typical Ethereum transaction hashing.
        return self.w3.eth.account.unsafe_sign_hash(hashed, self.keys.priv_key)

    def get_latest_nonce(self):
        """
        Retrieves the latest transaction count (nonce) for the client's Ethereum address.
        'pending' block identifier ensures that transactions that are already in the
        mempool but not yet mined are accounted for.

        Returns:
            int: The latest nonce for the client's address.
        """
        return self.w3.eth.get_transaction_count(self.keys.address, block_identifier='pending')

    def get_address_bytes(self):
        """
        Gets the client's Ethereum address in bytes format (without the '0x' prefix).

        Returns:
            bytes: The Ethereum address as bytes.
        """
        # Converts the hexadecimal address string (e.g., '0xabc...') to bytes by
        # removing the '0x' prefix and then converting from hex to bytes.
        return bytes.fromhex(self.keys.address[2:])

    def get_base_fee(self):
        """
        Retrieves the current base fee per gas from the latest block.
        This is part of the EIP-1559 transaction fee mechanism.

        Returns:
            int: The base fee per gas in Wei.
        """
        # Fetches the 'latest' block and extracts the 'baseFeePerGas' field.
        return self.w3.eth.get_block('latest')['baseFeePerGas']