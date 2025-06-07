import os.path

import blob
import ec
import keys
import model

# --- Configuration Section ---
chain_id = 1337  # Defines the Ethereum chain ID for the target network. 1337 is a common ID for local development networks (e.g., Ganache, Hardhat).
url = 'http://localhost:8545'  # Specifies the URL of the Ethereum node's RPC endpoint to connect to. This is a typical local address for development.
ethereum_data_dir = './projects/go-ethereum/data'  # The absolute or relative path to the Go-Ethereum (Geth) data directory.
# This directory is where Geth stores blockchain data and, crucially for this script, the encrypted keystore file.

# --- Key and Client Initialization ---
key_file = os.path.join(ethereum_data_dir,
                        'keystore/UTC--2025-06-07T23-18-27.738383000Z--71562b71999873db5b286df957af199ec94617f7')
# Constructs the full, OS-agnostic path to a specific Ethereum keystore file.
# This file contains the encrypted private key for the account that will sign transactions.

keys_supplier = keys.Keys.from_geth_file(key_file)
# Loads the Ethereum account keys from the specified Geth keystore file.
# The `keys_supplier` object will be used by the client for cryptographic signing operations.

client = ec.Client(url, keys_supplier)
# Initializes an Ethereum client object (`ec.Client`). This client connects to the specified `url`
# and is provided with the `keys_supplier` to manage the signing account.

# --- Transaction Parameter Preparation ---
start_nonce = client.get_latest_nonce()
# Retrieves the latest transaction count (nonce) for the client's associated Ethereum address.
# Nonces are critical for security, ensuring transactions are processed in a specific order and only once.

address = client.get_address_bytes()
# Gets the Ethereum address (in bytes format) associated with the loaded private key.

base_fee = client.get_base_fee()
# Fetches the current `baseFeePerGas` from the Ethereum network. This is a core component
# of the EIP-1559 gas fee mechanism, dynamically adjusting based on network utilization.

base_fee_per_blob_gas = client.get_base_fee_per_blob_gas()
# Retrieves the current `baseFeePerBlobGas` from the Ethereum network. This fee, introduced
# by EIP-4844 (Proto-Danksharding), dictates the minimum cost for including blob data.

tx_params = model.BaseTxParams(chain_id, nonce=start_nonce, gas=800000,
                               gas_tip_cap=base_fee + 1, gas_fee_cap=base_fee + 2)
# Creates an instance of `model.BaseTxParams`, representing the foundational parameters for an EIP-1559-style transaction.
# - `chain_id`: Ensures replay protection across different networks.
# - `nonce`: The transaction count for the sender.
# - `gas`: The maximum amount of gas units this transaction is allowed to consume.
# - `gas_tip_cap`: The maximum priority fee (in Wei per gas unit) the sender is willing to pay to the validator.
# - `gas_fee_cap`: The maximum total fee (in Wei per gas unit) the sender is willing to pay, covering both base fee and tip.

acc_list = [model.AccessTuple(bytes.fromhex('0000000000000000000000000000000000000001'), [
    bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000001')]).list()]
# Creates an Access List, as defined in EIP-2930. This list pre-specifies addresses and storage keys
# that the transaction is expected to access, potentially reducing gas costs.
# `.encode()` is called to prepare the AccessTuple for RLP encoding within the transaction.

# --- Blob Data Preparation ---
my_blob = b'hello blob'  # Defines the raw data that will be included as a blob in the transaction.
padded_blob, comm, proof = blob.blob_commitment_and_proof(my_blob)
if not padded_blob or not comm or not proof:
    raise 'couldn\'t commit and prove the blob'
# Calls a utility function (presumably from the 'blob' module) to process the raw blob data.
# - `padded_blob`: The raw blob data, padded to the required size for KZG polynomial computations.
# - `comm`: The KZG commitment (a cryptographic commitment) to the padded blob.
# - `proof`: The KZG proof, which allows verification of the blob's data against the commitment.

# --- Blob Transaction Construction ---
blob_tx = model.BlobTx(tx_params=tx_params, acc_list=acc_list, blob_fee_cap=base_fee_per_blob_gas + 1,
                       blob_hashes=[blob.kzg_to_versioned_hash(comm)],
                       sidecar=model.BlobSidecar(blobs=[padded_blob], commitments=[comm], proofs=[proof]))
# Constructs a `model.BlobTx` object, representing an EIP-4844 (Type 3) transaction.
# - `tx_params`: The base EIP-1559 transaction parameters.
# - `acc_list`: The optional EIP-2930 access list.
# - `blob_fee_cap`: The maximum fee per blob gas unit the sender is willing to pay. This is set
#                   slightly above the current `base_fee_per_blob_gas` to ensure inclusion.
# - `blob_hashes`: A list of versioned hashes of the KZG commitments to the blobs. These hashes
#                  are included in the transaction's execution payload.
# - `sidecar`: An instance of `model.BlobSidecar` containing the actual padded blobs, their KZG
#              commitments, and the corresponding KZG proofs. This data is transmitted separately
#              on the consensus layer.

# --- Transaction Signing and Sending ---
tx_hash = blob_tx.hash()
# Calculates the unique cryptographic hash of the constructed `BlobTx` object.
# This hash serves as the message that needs to be signed by the sender's private key.

signed = client.sign_hash(tx_hash)
# Signs the calculated `tx_hash` using the private key associated with the `client`'s loaded keys.
# The `signed` object typically contains the `v`, `r`, and `s` components of the elliptic curve digital signature.

raw = blob_tx.encode(keys.to_eth_v(signed.v), signed.r, signed.s)
# Encodes the complete `BlobTx` object into its raw RLP (Recursive Length Prefix) format.
# This raw format includes all transaction parameters and the `v`, `r`, `s` signature components.
# `keys.to_eth_v(signed.v)` is a helper function to ensure the `v` value (recovery ID) is
# in the correct EIP-155 compliant format for Ethereum transactions.
# The `raw` variable now holds the fully signed transaction, ready for broadcast.

print(client.send_signed_raw_transaction(raw, verbose=False))
# Sends the fully signed and RLP-encoded raw transaction bytes to the connected Ethereum node.
# The node will then propagate this transaction to the rest of the network for inclusion in a block.
# `verbose=False` suppresses detailed output from the send function.
