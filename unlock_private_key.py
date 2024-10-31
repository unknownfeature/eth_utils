from web3.auto import w3
with open('path to key file') as keyfile:
    encrypted_key = keyfile.read()
    private_key = w3.eth.account.decrypt(encrypted_key,
                                         'password')
    print(bytes.hex(private_key))
