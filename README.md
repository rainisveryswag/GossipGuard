# GossipGuard 🔐

> A post-quantum secure inter-process communication system combining McEliece asymmetric encryption with AES-256 symmetric encryption, transmitted over UNIX signals.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Performance](#performance)
- [Security Analysis](#security-analysis)
- [Limitations](#limitations)
- [Academic Context](#academic-context)

---

## Overview

GossipGuard is a proof-of-concept secure messaging system built around the **McEliece post-quantum cryptosystem**. It demonstrates how quantum-resistant cryptography can be integrated into real low-level applications using a hybrid encryption scheme.

**Key highlights:**
- Custom Python implementation of the McEliece cryptosystem (no external crypto libraries used for the core algorithm)
- Hybrid encryption: McEliece (asymmetric, post-quantum) + AES-256-CBC (symmetric)
- Inter-process communication via raw UNIX signals (SIGUSR1 / SIGUSR2), bit by bit
- Full object-oriented design following the Single Responsibility Principle
- Runs on Linux/Unix environments (Kali Linux tested)

**Why McEliece?**  
Classical asymmetric algorithms like RSA and ECC are vulnerable to Shor's algorithm on quantum computers. McEliece, based on the hardness of decoding random linear codes, has no known efficient quantum attack — making it a strong candidate for post-quantum cryptography. The NIST published its first post-quantum standards in August 2024; McEliece-family schemes are among the leading contenders.

---

## Architecture

```
GOSSIPGUARD/
├── GossipGuard/
│   ├── __init__.py
│   ├── client.py          # Encryption + signal transmission
│   └── server.py          # Signal reception + decryption
├── McElieceCipher/
│   ├── __init__.py
│   └── mceliece/          # Core McEliece implementation
│       └── ...
├── scripts/
│   ├── __init__.py
│   └── keygen.py          # Key pair generation
└── .venv/
```

### Layered Design

| Layer | Components | Responsibility |
|---|---|---|
| Application | `client.py`, `server.py` | Message flow, orchestration |
| Security | `McElieceCipher/`, AES | Hybrid encryption/decryption |
| Persistence | `scripts/keygen.py` | Key generation and storage |
| Communication | UNIX signal handler | Bit-by-bit IPC via SIGUSR1/SIGUSR2 |

---

## How It Works

### 1. Key Generation

```bash
python3 scripts/keygen.py
```

Generates the McEliece key pair:
- Generates a random generator matrix **G** for a linear error-correcting code
- Generates a random invertible matrix **S** (k×k) and permutation matrix **P** (n×n)
- Computes public key: **G' = S × G × P**
- Private key: **(S, G, P)**
- Saves to `public.key` and `private.key`

### 2. Hybrid Encryption (Client Side)

```
Plaintext message
      │
      ▼
[AES-256-CBC] ◄── random AES key (256-bit) + random IV
      │
      ▼
Ciphertext (Base64)
      │
      ▼
[McEliece encrypt] ◄── public.key
      │
      ▼
Payload: encrypted_AES_key | IV_b64 | ciphertext_b64
```

Each character of the payload is converted to 8 bits and transmitted to the server process via UNIX signals:
- **Bit 1** → `SIGUSR1`
- **Bit 0** → `SIGUSR2`

A null byte (`\0`) marks end-of-message.

### 3. Decryption (Server Side)

```
Received signals (SIGUSR1 / SIGUSR2)
      │
      ▼
Reconstruct bytes → full payload string
      │
      ▼
[McEliece decrypt] ◄── private.key → recover AES key
      │
      ▼
[AES-256-CBC decrypt] + remove PKCS7 padding
      │
      ▼
Plaintext message displayed in terminal
```

### McEliece Internals

**Encryption:**
```
c = m · G' + e
```
Where `m` is the message vector, `G'` is the public key, and `e` is a random error vector of weight `t`.

**Decryption:**
1. Apply inverse permutation: `c · P⁻¹`
2. Error-correct using the code's decoder → recover `m · S`
3. Multiply by `S⁻¹` → recover `m`

---

## Project Structure

### Classes

| Class | Responsibility |
|---|---|
| `McEliece` | Key generation, encrypt, decrypt — all core crypto logic |
| `Client` | Loads public key, encrypts message, transmits via signals |
| `Server` | Registers signal handlers, reconstructs payload, decrypts |
| `KeyManager` | Saves/loads key files |
| `AESEncryption` | AES-256-CBC encrypt/decrypt with PKCS7 padding |
| `SignalHandler` | Bit reconstruction from SIGUSR1/SIGUSR2 |
| `BinaryProtocol` | Encodes/decodes data for signal transmission |

---

## Installation

**Requirements:** Linux/Unix (tested on Kali Linux), Python 3.x

```bash
# Clone the repository
git clone https://github.com/rainisveryswag/GossipGuard.git
cd GossipGuard

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install cryptography
```

---

## Usage

### Step 1 — Generate keys

```bash
cd scripts
python3 keygen.py
# Output: public.key and private.key saved
```

### Step 2 — Start the server

```bash
cd GossipGuard
python3 server.py
# Output: SERVER PID: <pid>
#         Ready to receive encrypted messages...
```

### Step 3 — Send a message from the client

Open a second terminal:

```bash
cd GossipGuard
python3 client.py <SERVER_PID> "your message here"
```

The server terminal will display the decrypted message once all signals are received.

---

## Performance

Measured on a local machine (single system, Kali Linux):

| Operation | Average Time |
|---|---|
| McEliece key generation | ~4,280 ms |
| McEliece encryption (AES key) | ~870 ms |
| McEliece decryption | ~136 ms |
| AES encryption | ~32 ms/KB |
| AES decryption | ~28 ms/KB |
| Signal transmission | ~120 ms/byte |

**Resource usage:**
- Server memory: ~28 MB average
- Client memory: ~24 MB average
- Peak (matrix generation): ~45 MB
- Public key size: ~512 KB
- Private key size: ~256 KB

The main bottleneck is signal-based transmission (~12.5 bytes/sec), which is inherent to the bit-by-bit IPC mechanism and intentional for this proof-of-concept.

---

## Security Analysis

### Strengths

- **Post-quantum resistance**: McEliece is based on the NP-hard problem of decoding random linear codes. No known quantum algorithm (including Shor's) significantly weakens it.
- **Hybrid scheme**: AES-256-CBC handles bulk data efficiently; McEliece protects only the small AES key — best of both worlds.
- **Random IV per message**: Prevents pattern attacks; identical plaintexts produce different ciphertexts.
- **No network exposure**: Signal-based IPC requires local access, eliminating most remote attack vectors.
- **PKCS7 padding**: Standard padding scheme for AES-CBC block alignment.

### Known Limitations (by design — academic scope)

- Simplified McEliece parameters (smaller matrices than production recommendations)
- No authentication mechanism (sender identity not verified)
- Key files stored on disk with OS-level permissions
- No protection against timing side-channel attacks
- No HMAC / message integrity verification

---

## Limitations

- **Linux/Unix only**: Relies on POSIX signals (`SIGUSR1`/`SIGUSR2`); not compatible with Windows
- **Local IPC only**: Signals cannot cross machine boundaries
- **Low throughput**: ~12.5 bytes/sec transmission speed due to signal delays
- **No error detection on lost signals**: A dropped signal corrupts the message silently
- **Simplified McEliece**: Uses reduced parameters for pedagogical clarity, not production-grade security

---

## Academic Context

Developed as part of the **Object-Oriented Programming and Advanced Python Algorithms for Security** module at:

> École Nationale des Sciences Appliquées de Marrakech (ENSA Marrakech)  
> Université Cadi Ayyad — Génie Cyber Défense & Systèmes de Télécommunication Embarquée  
> Academic Year 2024–2025

**Supervised by:** Pr. Ali Azougaghe

**Team:** Youssra Zarri, Amal SAB, Hiba SIDINOU, Oussama BAGY, Noussair BOUANANI, Fatima Ezzahra ENNASSIRI

---

*GossipGuard is a proof-of-concept educational project. Do not use in production environments.*
