# Ethereum Interaction Library

This repository contains a Python library for interacting with the Ethereum blockchain, offering functionalities for sending custom transactions, deploying and interacting with smart contracts, and managing Ethereum account keys. It includes support for modern Ethereum transaction types like EIP-1559 and EIP-4844 (Blob Transactions), alongside custom transaction types.

---

## Features

* **Ethereum Client:** Connects to an Ethereum node and handles transaction signing and broadcasting.
* **Key Management:** Securely loads Ethereum account keys from Geth-style keystore files or directly from private keys.
* **Transaction Building:**
    * **Base Transaction Parameters:** Defines common parameters for EIP-1559 transactions (chain ID, nonce, gas limits).
    * **Access Tuples:** Supports EIP-2930 access lists for optimizing gas costs.
    * **Blob Transactions (EIP-4844):** Constructs and signs transactions with associated data blobs, crucial for Layer 2 scaling solutions.
    * **Custom `SetCodeTx`:** A specialized transaction type (likely for account abstraction or custom protocol interactions) enabling programmatic code setting.
* **Smart Contract Interaction:**
    * **Deployment:** Easily deploy smart contracts to the network.
    * **Function Calls:** Transact with state-changing contract functions.
    * **Read-Only Calls:** Execute view/pure contract functions to read blockchain state without sending a transaction.
* **Signature Utilities:** Provides helpers for calculating function selectors and adjusting the `v` component of signatures for EIP-155 replay protection.

---

## Installation

To get started with this library, you'll need Python 3.8+ and the necessary dependencies.

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/unknownfeature/eth_utils
    cd eth_utils
    ```

2.  **Install dependencies:**

    ```bash
    pip install web3 rlp eth-hash[auto] eth-typing
    ```
    or
    ```bash
    pip install -r requirements.txt
    ```
    * `web3`: The primary Python library for interacting with Ethereum.
    * `rlp`: Used for Recursive Length Prefix encoding, fundamental to Ethereum's data serialization.
    * `eth-hash[auto]`: Provides the Keccak hashing algorithm.
    * `eth-typing`: Ethereum-specific type annotations.

---

## Usage

This library is designed for programmatic interaction with an Ethereum node. Here's a quick overview of how you might use its core components.

### Connecting to Ethereum

Example

```python
import os
import ec 
import keys

# Configuration
chain_id = 1337 # Example: Local Ganache/Hardhat network ID
url = 'http://localhost:8545' # Your Ethereum node RPC URL

# Path to your Geth keystore file (replace with your actual path)
# IMPORTANT: Never hardcode private keys or passwords in production.
# Use environment variables or secure key management solutions.
ethereum_data_dir = './projects/go-ethereum/data' # Example path
key_file = os.path.join(ethereum_data_dir,
                        'keystore/UTC--2025-05-15T23-57-15.101054000Z--13226a7e8843bf69e16cd0129ca421e92e86f083') #example key name

# Load keys from a Geth keystore file (or use Keys.from_address_and_private_key)
keys_supplier = keys.Keys.from_geth_file(key_file, pswd='') # Add your password if necessary

# Initialize the client
client = ec.Client(url, keys_supplier)

print(f"Connected to Ethereum node: {client.w3.is_connected()}")
print(f"Client Address: {client.get_address_bytes().hex()}")
```
#### *See examples folder for more examples