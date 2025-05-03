#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import signal
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from McElieceCipher.mceliece.mceliece import McEliece


class SecureServer:
    def __init__(self):
        self.binary_buffer = ""  # Ensure this is initialized here
        self.received_data = bytearray()
        self.mc = McEliece()

        self.private_key_path = "private.key"
        if not os.path.exists(self.private_key_path):
            print(" No keys found. Please run keygen.py first.")
            sys.exit(1)

        self._load_keys()


    def _load_keys(self):
        try:
            with open(self.private_key_path, 'rb') as f:
                key_data = f.read()
            self.mc.load_private_key(key_data)
        except Exception as e:
            print(f"Failed to load keys: {e}")
            sys.exit(1)

    def handle_signal(self, signum, frame):
        """
        Handle incoming signals (SIGUSR1 for 1, SIGUSR2 for 0).
        Collect bits until we receive a complete byte, then process the message.
        """
        bit = '1' if signum == signal.SIGUSR1 else '0'
        self.binary_buffer += bit

        if len(self.binary_buffer) == 8:
            try:
                byte = int(self.binary_buffer, 2)
                self.binary_buffer = ""
                if byte == 0:
                    self._process_message()
                else:
                    self.received_data.append(byte)
            except ValueError:
                print("Invalid binary data received.")
                self.binary_buffer = ""

    def _process_message(self):
        if not self.received_data:
            return

        try:
            # Decode the message using latin1 to avoid UTF-8 issues
            encrypted_string = self.received_data.decode('latin1')
            print(f"\n Raw message received:\n{encrypted_string}")

            # Split the message into 3 parts: AES key, IV, and ciphertext
            parts = encrypted_string.split('|')
            if len(parts) != 3:
                print(f"Invalid message format. Expected 3 parts, but got {len(parts)}. Message: {encrypted_string}")
                return

            enc_aes_key_str, iv_b64, cipher_b64 = parts
            print(f"Encrypted AES Key: {enc_aes_key_str}")
            print(f"IV: {iv_b64}")
            print(f"Ciphertext: {cipher_b64}")

            # Decrypt AES key with McEliece
            decrypted_key_hex = self.mc.decrypt(enc_aes_key_str)
            aes_key = bytes.fromhex(decrypted_key_hex)
            print(f"Decrypted AES Key (hex): {aes_key.hex()}")

            # Decode the IV and ciphertext from base64
            iv = base64.b64decode(iv_b64)
            ciphertext = base64.b64decode(cipher_b64)
            print(f"IV (decoded): {iv.hex()}")
            print(f"Ciphertext (decoded): {ciphertext.hex()}")

            # Decrypt the AES-encrypted message
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

            print(f"\n[SERVER] Decrypted Message:\n{plaintext.decode('utf-8')}")

        except Exception as e:
            print(f"\n Decryption failed: {e}")
        finally:
            self.received_data.clear()

    def run(self):
        print(r"""
  ____               _        ____                     _ 
 / ___| ___  ___ ___(_)_ __  / ___|_   _  __ _ _ __ __| |
| |  _ / _ \/ __/ __| | '_ \| |  _| | | |/ _` | '__/ _` |
| |_| | (_) \__ \__ \ | |_) | |_| | |_| | (_| | | | (_| |
 \____|\___/|___/___/_| .__/ \____|\__,_|\__,_|_|  \__,_|
                      |_|                                
""")
        print(f"SERVER PID: {os.getpid()}")
        print("Ready to receive encrypted messages...\n")

        signal.signal(signal.SIGUSR1, self.handle_signal)
        signal.signal(signal.SIGUSR2, self.handle_signal)

        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            print("\n Server shutting down.")
            sys.exit(0)


if __name__ == "__main__":
    server = SecureServer()
    server.run()