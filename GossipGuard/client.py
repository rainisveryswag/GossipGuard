#!/usr/bin/env python3
import os
import sys
import time
import signal
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# :white_check_mark: Fix import path for McEliece
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from McElieceCipher.mceliece.mceliece import McEliece

# :white_check_mark: Load existing public key (not generate new ones)
mc = McEliece()
with open("public.key", "rb") as f:
    public_key_data = f.read()
mc.load_public_key(public_key_data)


def encrypt_with_aes(message, key):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv, ciphertext


def send_signal(pid, char):
    for i in reversed(range(8)):  # MSB to LSB
        bit = (ord(char) >> i) & 1
        sig = signal.SIGUSR1 if bit else signal.SIGUSR2
        try:
            os.kill(pid, sig)
        except Exception:
            sys.stderr.write(":x: Error: Invalid PID or signal failed!\n")
            sys.exit(1)
        time.sleep(0.1)


def send_message(pid, message):
    aes_key = os.urandom(32)  # 256-bit AES key
    iv, ciphertext = encrypt_with_aes(message, aes_key)

    # :white_check_mark: Fix: convert AES key to hex string before encryption
    encrypted_key = mc.encrypt(aes_key.hex())

    payload = {
        "k": encrypted_key,
        "v": base64.b64encode(iv).decode(),
        "c": base64.b64encode(ciphertext).decode()
    }
    full_message = f'{payload["k"]}|{payload["v"]}|{payload["c"]}'
    print(f":rocket: Sending: {full_message}")

    for char in full_message:
        send_signal(pid, char)
    send_signal(pid, '\0')  # End


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: python3 client.py <Server_PID> <Message>\n")
        sys.exit(1)

    pid = int(sys.argv[1])
    send_message(pid, sys.argv[2])