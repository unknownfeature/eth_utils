import os.path
import ec
import keys
import model

# --- Configuration Section ---
chain_id = 1337  # Defines the Ethereum chain ID. 1337 is commonly used for local development networks (e.g., Ganache, Hardhat).
url = 'http://localhost:8545'  # Specifies the URL of the Ethereum node to connect to. This is a typical local RPC endpoint.
ethereum_data_dir =  './projects/go-ethereum/data' # The actual path to the Go-Ethereum (Geth) data directory.
                                                         # This directory contains the keystore file.

# --- Key and Client Initialization ---
key_file = os.path.join(ethereum_data_dir,
                        'keystore/UTC--2025-06-07T23-18-27.738383000Z--71562b71999873db5b286df957af199ec94617f7')
# Constructs the full path to the Ethereum keystore file using os.path.join for OS compatibility.
# This file contains the encrypted private key for an Ethereum account.

keys_supplier = keys.Keys.from_geth_file(key_file) # Loads the Ethereum account keys from the specified Geth keystore file.
                                                    # This object will be used for signing transactions.

client = ec.Client(url, keys_supplier) # Initializes an Ethereum client object, connecting to the specified URL
                                        # and providing it with the loaded keys for transaction signing.

# --- Transaction Parameter Preparation ---
start_nonce = client.get_latest_nonce() # Retrieves the latest transaction count (nonce) for the client's address.
                                        # Nonces are used to ensure transactions are processed in order and only once.

address = client.get_address_bytes() # Gets the Ethereum address associated with the loaded keys, in bytes format.

base_fee = client.get_base_fee() # Fetches the current base fee from the Ethereum network.
                                  # The base fee is part of the EIP-1559 gas fee mechanism.

num_of_authorizations = 2 # Defines the number of `SetCodeAuthorization` objects to create.

tx_params = model.BaseTxParams(chain_id, nonce=start_nonce, gas=800000,
                               gas_tip_cap=base_fee + 1, gas_fee_cap=base_fee + 2)
# Creates a base transaction parameters object.
# - chain_id: The ID of the network.
# - nonce: The transaction nonce, starting from the current latest nonce.
# - gas: The maximum amount of gas the transaction is allowed to consume.
# - gas_tip_cap: The maximum priority fee (tip) per gas unit the sender is willing to pay to the validator.
# - gas_fee_cap: The maximum total fee per gas unit the sender is willing to pay (base fee + tip).

acc_list = [model.AccessTuple(bytes.fromhex('0000000000000000000000000000000000000001'), [
    bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000001')]).list()]

# Defines an Access List for the transaction. Access lists specify which addresses and storage keys
# a transaction is expected to access, potentially reducing gas costs.
# This example uses placeholder addresses/keys.

# --- Authorization Creation ---
auths = [model.SetCodeAuthorization(chain_id=chain_id, addr=address, nonce=start_nonce + i + 1,
                                    signing_function=client.sign_hash).list()
         for i in range(num_of_authorizations)]

# Generates a list of `SetCodeAuthorization` objects. These are specific types of authorizations
#  that might allow changing contract code.
# Each authorization has:
# - chain_id: The network ID.
# - addr: The address associated with the authorization (likely the sender's address).
# - nonce: A unique nonce for each authorization, incrementing from `start_nonce + 1`.
# - signing_function: A reference to the client's `sign_hash` method to sign the authorization.
# `.encode()` is called on each authorization to serialize it.

# --- Transaction Construction, Signing, and Sending ---
set_code_tx = model.SetCodeTx(tx_params=tx_params, acc_list=acc_list,
                              set_code_auth_list=auths)
# Constructs the `SetCodeTx` transaction object, bundling the base transaction parameters,
# the access list, and the generated `SetCodeAuthorization` list.

tx_hash = set_code_tx.hash() # Calculates the cryptographic hash of the transaction.
                              # This hash uniquely identifies the transaction before it's signed.

signed = client.sign_hash(tx_hash) # Signs the transaction hash using the private key loaded into the client.
                                    # The result (`signed`) typically contains the `v`, `r`, and `s` components
                                    # of the elliptic curve digital signature.

raw = set_code_tx.encode(keys.to_eth_v(signed.v), signed.r, signed.s)
# Encodes the complete transaction object, incorporating the `v`, `r`, and `s` signature components.
# `keys.to_eth_v(signed.v)` might be a helper function to ensure the `v` value is in the correct Ethereum format.
# This `raw` variable now holds the fully signed and RLP-encoded transaction ready for broadcast.

client.send_signed_raw_transaction(raw) # Sends the fully signed and raw transaction bytes to the Ethereum node.
                                        # The node will then broadcast it to the network for mining.