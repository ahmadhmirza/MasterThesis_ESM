# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#                            ROBERT BOSCH GMBH                              #
#                                STUTTGART                                  #
#                                                                           #
#              Alle Rechte vorbehalten - All rights reserved                #
#                                                                           #
#############################################################################
#                      ____   ____  _____  ______ __  __                    #
#                     / __ ) / __ \/ ___/ / ____// / / /                    #
#                    / __  |/ / / /\__ \ / /    / /_/ /                     #
#                   / /_/ // /_/ /___/ // /___ / __  /                      #
#                  /_____/ \____//____/ \____//_/ /_/                       #
#                                                                           #
#############################################################################

"""
Created on Mon Feb 10 13:13:13 2020
@author: Ahmad H. Mirza(PS-EC/ECC) [Mir6si]
--------------------------------------------
Script to generate Signatues for files
Parameters : File path + Encoding Key

python util_Generate_Signature.py <FilePath> <Key>
--------------------------------------------
scriptVersion = 1.0.0
"""

import hmac
from hashlib import md5
from optparse import OptionParser

def generateSignature(filePath,mKey):
    h = hmac.new(mKey.encode(),msg = None,digestmod=md5)
    with open(filePath,"rb") as f:  
        for chunk in iter(lambda: f.read(4096), b""):
           h.update(chunk)
    return h.hexdigest()


def main():
    usage = "usage: %prog arg1<FilePath> arg2<EncodingKey>"
    parser = OptionParser(usage=usage)
    (options, args)   = parser.parse_args()
    if len(args) != 2:
        print("Incorrect number of arguments provided!")
    else:
        filePath    = str(args[0])
        mEncodingKey = str(args[1])
     
    signature = generateSignature(filePath,mEncodingKey)
    
    #print("Signature for the selected file:")
    print(str(signature))
    #return signature
        
if __name__ == '__main__':
    main()