import base64
import socket
import zlib
from SimpleXMLRPCServer import SimpleXMLRPCServer
import logging
import psutil
import re
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class Worker:

    def __init__(self):
        self.filePath = '/mnt/nfs/penelitian2019/'
        self.rawFilePath = 'raw-file/'
        self.keyFilePath = 'key-file/'
        self.encryptedFilePath = 'enc-file/'
        self.decryptedFilePath = 'dec-file/'
        print('-- System Initialized --')
        logging.debug('-- System Initialized --')

    def encrypt_blob(self, blob, public_key):
        # Import the Public Key and use for encryption using PKCS1_OAEP
        rsa_key = RSA.importKey(public_key)
        rsa_key = PKCS1_OAEP.new(rsa_key)

        # compress the data first
        blob = zlib.compress(blob)

        # In determining the chunk size, determine the private key length used in bytes
        # and subtract 42 bytes (when using PKCS1_OAEP). The data will be in encrypted
        # in chunks
        chunk_size = 470
        offset = 0
        end_loop = False
        encrypted = ""

        while not end_loop:
            # The chunk
            chunk = blob[offset:offset + chunk_size]

            # If the data chunk is less then the chunk size, then we need to add
            # padding with " ". This indicates the we reached the end of the file
            # so we end loop here
            if len(chunk) % chunk_size != 0:
                end_loop = True
                chunk += " " * (chunk_size - len(chunk))

            # Append the encrypted chunk to the overall encrypted file
            encrypted += rsa_key.encrypt(chunk)

            # Increase the offset by chunk size
            offset += chunk_size

        # Base 64 encode the encrypted file
        return base64.b64encode(encrypted)

    def do_EncryptFile(self, fileNameToEnc, fileName):
        print('-- Encrypting ' + fileNameToEnc + ' --')
        logging.debug('Start: Encrypting ' + fileNameToEnc)
        keyName = 'pub' + fileName + '.pem'
        # print keyName
        print('-- Opening Public Key For ' + fileName + ' --')
        logging.debug('Start: Opening Public Key For ' + fileName)
        fd = open(self.filePath + self.keyFilePath + keyName, 'rb')
        public_key = fd.read()
        fd.close()

        print('-- Reading Binary File ' + fileNameToEnc + ' --')
        logging.debug('Start: Reading Binary File ' + fileNameToEnc)
        # Our candidate file to be encrypted
        fd = open(self.filePath + self.rawFilePath + fileNameToEnc, 'rb')
        unencrypted_blob = fd.read()
        fd.close()

        print('-- Now Encrypting ' + fileNameToEnc + ' --')
        logging.debug('Start: Now Encrypting ' + fileNameToEnc)
        encrypted_blob = self.encrypt_blob(unencrypted_blob, public_key)

        # Write the encrypted contents to a file
        print('-- Write Encrypted File ' + fileNameToEnc + ' --')
        logging.debug('Start: Write Encrypted File ' + fileNameToEnc)
        fd = open(self.filePath + self.encryptedFilePath + fileNameToEnc, 'wb')
        fd.write(encrypted_blob)
        fd.close()
        print('-- Done Ecrypting ' + fileNameToEnc + ' --')
        logging.debug('Finish: Done Ecrypting ' + fileNameToEnc)
        return 'Done'

    def decrypt_blob(self, blob, private_key):
        # Import the Private Key and use for decryption using PKCS1_OAEP
        rsakey = RSA.importKey(private_key)
        rsakey = PKCS1_OAEP.new(rsakey)

        # Base 64 decode the data
        encrypted_blob = base64.b64decode(blob)

        # In determining the chunk size, determine the private key length used in bytes.
        # The data will be in decrypted in chunks
        chunk_size = 512
        offset = 0
        decrypted = ""

        # keep loop going as long as we have chunks to decrypt
        while offset < len(encrypted_blob):
            # The chunk
            chunk = encrypted_blob[offset: offset + chunk_size]

            # Append the decrypted chunk to the overall decrypted file
            decrypted += rsakey.decrypt(chunk)

            # Increase the offset by chunk size
            offset += chunk_size

        # return the decompressed decrypted data
        return zlib.decompress(decrypted)

    def do_DecryptFile(self, fileNameToDec, fileName):
        print('-- Decrypting ' + fileNameToDec + ' --')
        logging.debug('Start: Decrypting ' + fileNameToDec)
        keyName = 'priv' + fileName + '.pem'

        # Use the private key for decryption
        print('-- Opening Private Key For ' + fileName + ' --')
        logging.debug('Start: Opening Private Key For ' + fileName)
        fd = open(self.filePath + self.keyFilePath + keyName, 'rb')
        private_key = fd.read()
        fd.close()

        print('-- Reading Binary File ' + fileNameToDec + ' --')
        logging.debug('Start: Reading Binary File ' + fileNameToDec)
        # Our candidate file to be decrypted
        fd = open(self.filePath + self.encryptedFilePath + fileNameToDec, 'rb')
        encrypted_blob = fd.read()
        fd.close()

        print('-- Now Decrypting and Write File ' + fileNameToDec + ' --')
        logging.debug('Start: Now Decrypting and Write File ' + fileNameToDec)
        # Write the decrypted contents to a file
        fd = open(self.filePath + self.decryptedFilePath + fileNameToDec, 'wb')
        fd.write(self.decrypt_blob(encrypted_blob, private_key))
        fd.close()
        print('-- Done Decrypting ' + fileNameToDec + ' --')
        logging.debug('Finish: Done Decrypting ' + fileNameToDec)
        return 'Done'

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

logging.basicConfig(filename=IPAddr + '_run.log', format='%(asctime)s %(message)s',level=logging.DEBUG)

server = SimpleXMLRPCServer((IPAddr, 8000), logRequests=True, allow_none=True);
server.register_multicall_functions()
server.register_instance(Worker())

try:
    print 'Use Control-C to exit'
    print 'Your Computer IP Address is:' + IPAddr
    server.serve_forever()
except KeyboardInterrupt:
    print 'Exiting'
