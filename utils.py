import json
from eth_hash.auto import keccak

from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))


class Keys:
    def __init__(self, pub_key, priv_key):
        self.address = Web3.to_checksum_address(pub_key)
        self.priv_key = priv_key


def read_contract_json(file_name: str) -> dict:
    with open(file_name, 'r') as fle:
        return json.load(fle)


def deploy_contract(contract_json, *params, gas: int = 11000000, keys: Keys, get_abi=lambda x: x['abi'], value=0,
                    get_bytecode=lambda x: x['bytecode']) -> str:
    nonce = w3.eth.get_transaction_count(keys.address, block_identifier='pending')
    contract = w3.eth.contract(abi=get_abi(contract_json), bytecode=get_bytecode(contract_json))
    transaction = contract.constructor(*params).build_transaction(
        {'from': keys.address, 'nonce': nonce, 'gas': gas, 'value': value})
    signed_txn = w3.eth.account.sign_transaction(transaction, keys.priv_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress


def transact_function(contract_address, contract_abi, function_name, *params, gas: int = 8000000, keys: Keys, value=0,
                      verbose=True, ):
    nonce = w3.eth.get_transaction_count(keys.address, block_identifier='pending')
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    transaction = contract.functions[function_name](*params).build_transaction(
        {"from": keys.address, 'nonce': nonce, 'gas': gas, 'value': value})
    signed_txn = w3.eth.account.sign_transaction(transaction, keys.priv_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if verbose:
        print(
            f'called {function_name} on {contract_address} with params: {params} and status {receipt.status}\n')
    return receipt


def call_function(contract_address, contract_abi, function_name, *params, verbose=True):
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    res = contract.functions[function_name](*params).call({'to': contract_address},
                                                          block_identifier='pending')
    if verbose:
        print(f'{contract_address}.{function_name} {params} = {res}\n')
    return res


def get_type_def_from_encode(abi_json, filter_func, mapper_func):
    type_def = next(map(mapper_func, filter(filter_func, abi_json)))
    return flatten_type_def(type_def)


def flatten_type_def(item):
    if 'components' in item:
        return '(' + ','.join(flatten_type_def(x) for x in item['components']) + ')'

    return item['type']


def get_function_selector(function_signature):
    return keccak(function_signature.encode())[:4]
