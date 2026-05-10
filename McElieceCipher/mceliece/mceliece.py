import os
import base64

class McEliece:
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.key_size = 32  # AES-256 = 32 bytes

    def generate_keys(self):
        # Generate a mock private key
        self.private_key = os.urandom(self.key_size)
        # The public key is just a reversed private key (so it's invertible)
        self.public_key = self.private_key[::-1]
        return {"public_key": self.public_key}, {"private_key": self.private_key}

    def save_keys(self, priv_path, pub_path):
        with open(priv_path, "wb") as f:
            f.write(self.private_key)
        with open(pub_path, "wb") as f:
            f.write(self.public_key)

    def load_private_key(self, data: bytes):
        self.private_key = data
        self.public_key = data[::-1]

    def load_public_key(self, data: bytes):
        self.public_key = data
        self.private_key = data[::-1]

    def encrypt(self, aes_key_hex: str) -> str:
        aes_key = bytes.fromhex(aes_key_hex)
        encrypted = bytearray()
        for i, b in enumerate(aes_key):
            encrypted.append(b ^ self.public_key[i % self.key_size])
        return base64.b64encode(bytes(encrypted)).decode()

    def decrypt(self, encrypted_b64: str) -> str:
        encrypted = base64.b64decode(encrypted_b64)
        decrypted = bytearray()
        # Reverse private key to get the public key used for encryption
        public_key = self.private_key[::-1]
        for i, b in enumerate(encrypted):
            decrypted.append(b ^ public_key[i % self.key_size])
        return decrypted.hex()