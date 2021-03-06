from toolbox.symcrypto import AuthenticatedCryptoAbstraction
from toolbox.pairinggroup import *
from charm.pairing import hash as sha1
from schemes.ibenc_adapt_identityhash import *
from toolbox.IBEnc import *
from charm.cryptobase import *
from math import ceil

debug = False
class HybridIBEnc(IBEnc):
    def __init__(self, scheme, groupObj):
        global ibenc, group
        ibenc = scheme
        group = groupObj

    def setup(self):
        return ibenc.setup()
    
    def extract(self, mk, ID):
        return ibenc.extract(mk, ID)
    
    def encrypt(self, pk, ID, M):
        if type(M) != str: raise "message not right type!"        
        key = group.random(GT)
        c1 = ibenc.encrypt(pk, ID, key)
        # instantiate a symmetric enc scheme from this key
        cipher = AuthenticatedCryptoAbstraction(sha1(key))
        c2 = cipher.encrypt(M)
        return { 'c1':c1, 'c2':c2 }
    
    def decrypt(self, pk, ID, ct):
        c1, c2 = ct['c1'], ct['c2']
        key = ibenc.decrypt(pk, ID, c1)        
        cipher = AuthenticatedCryptoAbstraction(sha1(key))
        return cipher.decrypt(c2)
    
def main():
    groupObj = PairingGroup('SS512')
    ibe = IBE_BB04(groupObj)
    
    hashID = HashIDAdapter(ibe, groupObj)
    
    hyb_ibe = HybridIBEnc(hashID, groupObj)
    
    (pk, mk) = hyb_ibe.setup()

    kID = 'waldoayo@gmail.com'
    sk = hyb_ibe.extract(mk, kID)

    msg = "Hello World My name is blah blah!!!! Word!"
    
    ct = hyb_ibe.encrypt(pk, sk['id'], msg)
    if debug:
        print("Ciphertext")
        print("c1 =>", ct['c1'])
        print("c2 =>", ct['c2'])
    
    orig_msg = hyb_ibe.decrypt(pk, sk, ct)
    if debug: print("Result =>", orig_msg)
    assert orig_msg == msg
    del groupObj

if __name__ == "__main__":
    debug = True
    main()

    
    
