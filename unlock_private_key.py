from web3.auto import w3
with open('/Users/anya/projects/go-ethereum/datadir/keystore/UTC--2024-11-27T23-02-48.728664000Z--bea39b029b125aa100b63e1efc5ae026ad62ef60') as keyfile:
    encrypted_key = keyfile.read()
    private_key = w3.eth.account.decrypt(encrypted_key,
                                         'password12345')
    print(bytes.hex(private_key))
#