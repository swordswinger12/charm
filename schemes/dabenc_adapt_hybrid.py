from toolbox.symcrypto import AuthenticatedCryptoAbstraction
from charm.cryptobase import *
from charm.pairing import hash as sha1
from math import ceil
from schemes.dabe_aw11 import Dabe
from toolbox.ABEncMultiAuth import ABEncMultiAuth
from toolbox.pairinggroup import *

debug = False
class HybridABEncMA(ABEncMultiAuth):
    def __init__(self, scheme, groupObj):
        global abencma, group
        # check properties (TODO)
        abencma = scheme
        group = groupObj

    def setup(self):
        return abencma.setup()
    
    def authsetup(self, gp, attributes):
        return abencma.authsetup(gp, attributes)
    
    def keygen(self, gp, sk, i, gid, pkey):
        return abencma.keygen(gp, sk, i, gid, pkey)

    def encrypt(self, pk, gp, M, policy_str):
        if type(M) != str and type(policy_str) != str: raise "message and policy not right type!"        
        key = group.random(GT)
        c1 = abencma.encrypt(pk, gp, key, policy_str)
        # instantiate a symmetric enc scheme from this key
        cipher = AuthenticatedCryptoAbstraction(sha1(key)) 
        c2 = cipher.encrypt(M)
        return { 'c1':c1, 'c2':c2 }
    
    def decrypt(self, gp, sk, ct):
        c1, c2 = ct['c1'], ct['c2']
        key = abencma.decrypt(gp, sk, c1)
        cipher = AuthenticatedCryptoAbstraction(sha1(key))
        return cipher.decrypt(c2)
        
def main():
    groupObj = PairingGroup('../param/a.param')
    dabe = Dabe(groupObj)
        
    hyb_abema = HybridABEncMA(dabe, groupObj)
    
    #Setup global parameters for all new authorities
    gp = hyb_abema.setup()
    
    #Instantiate a few authorities 
    #Attribute names must be globally unique.  HybridABEncMA
    #Two authorities may not issue keys for the same attribute. 
    #Otherwise, the decryption algorithm will not know which private key to use   
    jhu_attributes = ['jhu_professor', 'jhu_staff', 'jhu_student']
    jhmi_attributes = ['jhmi_doctor', 'jhmi_nurse', 'jhmi_staff', 'jhmi_researcher']
    (jhuSK, jhuPK) = hyb_abema.authsetup(gp, jhu_attributes)
    (jhmiSK, jhmiPK) = hyb_abema.authsetup(gp, jhmi_attributes)
    allAuthPK = {}; allAuthPK.update(jhuPK); allAuthPK.update(jhmiPK)
    
    #Setup a user with a few keys
    bobs_gid = "20110615 bob@gmail.com cryptokey"
    K = {}
    hyb_abema.keygen(gp, jhuSK,'jhu_professor', bobs_gid, K)
    hyb_abema.keygen(gp, jhmiSK,'jhmi_researcher', bobs_gid, K)
    
    
    msg = 'Hello World, I am a sensitive record!'
    size = len(msg)
    policy_str = "(jhmi_doctor or (jhmi_researcher and jhu_professor))"
    ct = hyb_abema.encrypt(allAuthPK, gp, msg, policy_str)    

    if debug:
        print("Ciphertext")
        print("c1 =>", ct['c1'])
        print("c2 =>", ct['c2'])
    
    orig_msg = hyb_abema.decrypt(gp, K, ct)
    if debug: print("Result =>", orig_msg)
    assert orig_msg == msg, "Failed Decryption!!!"
    if debug: print("Successful Decryption!!!")
    del groupObj

if __name__ == "__main__":
    debug = True
    main()
