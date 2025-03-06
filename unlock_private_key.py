from web3.auto import w3

with open('/var/folders/rx/9sm3kk3970v4vsy8tsvv3gxw0000gn/T/go-ethereum-keystore118401165/UTC--2025-02-27T22-12-18.625668000Z--ae3057a07ff3f721dfe2892a488a3dce679cfa3e') as keyfile:
    encrypted_key = keyfile.read()
    private_key = w3.eth.account.decrypt(encrypted_key,
                                         'password12345')
    print(bytes.hex(private_key))
