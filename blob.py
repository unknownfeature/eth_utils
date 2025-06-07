import hashlib

import requests
from ckzg import (
    blob_to_kzg_commitment,
    compute_blob_kzg_proof,
    load_trusted_setup, verify_blob_kzg_proof,
)

# --- ckz constants ---
BYTES_PER_FIELD_ELEMENT = 32
FIELD_ELEMENTS_PER_BLOB = 4096
# --- Constants for EIP-4844 ---
# Total size of a blob in bytes (4096 field elements * 32 bytes/field element)
BLOB_FULL_SIZE_BYTES = FIELD_ELEMENTS_PER_BLOB * BYTES_PER_FIELD_ELEMENT
# The version byte for KZG-versioned hashes
VERSIONED_HASH_VERSION_KZG = 0x01

# the script with download c-kzg from git and save it to this file
trusted_setup_location = 'trusted_setup.txt'

with open(trusted_setup_location, 'w') as fl:
    fl.write(requests.get('https://raw.githubusercontent.com/ethereum/c-kzg-4844/37140215cd6fcd99363b7f02bf52f8bf7f6f5968/src/trusted_setup.txt').text)

# loadind trusted setup
kzg_settings = load_trusted_setup(trusted_setup_location, 6)


def prepare_blob_data(input_data: str) -> bytes:
    """
    Prepares the input string data into a 128KB blob (padded).
    Blobs are conceptually 4096 field elements, each 32 bytes.
    The input data should be byte-encoded and then padded.
    """
    # Convert input string to bytes
    encoded_data = input_data.encode('utf-8')

    # Calculate padding needed
    # A blob must be exactly BLOB_FULL_SIZE_BYTES
    if len(encoded_data) > BLOB_FULL_SIZE_BYTES:
        raise ValueError(f"Input data too large for a single blob. Max: {BLOB_FULL_SIZE_BYTES} bytes")

    # Pad with zeros
    padded_data = encoded_data + b'\x00' * (BLOB_FULL_SIZE_BYTES - len(encoded_data))
    return padded_data


def kzg_to_versioned_hash(kzg_commitment: bytes) -> bytes:
    """
    Converts a KZG commitment to a versioned hash.
    Versioned hash is 0x01 byte + last 31 bytes of sha256(commitment).
    """
    sha256_hash = hashlib.sha256(kzg_commitment).digest()
    versioned_hash = bytes([VERSIONED_HASH_VERSION_KZG]) + sha256_hash[1:]
    return versioned_hash

padded_blob_bytes = prepare_blob_data('123456')
kzg_commitment = blob_to_kzg_commitment(padded_blob_bytes, kzg_settings)
kzg_proof = compute_blob_kzg_proof(padded_blob_bytes, kzg_commitment, kzg_settings)
print(verify_blob_kzg_proof(padded_blob_bytes, kzg_commitment, kzg_proof, kzg_settings))