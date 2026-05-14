# core/crypto.py
# Heart of DEM - handles all encryption and decryption
# Uses AES-256-GCM with chunked streaming so even 10GB files work fine

import os
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Magic bytes that identify a .dem file
MAGIC = b"DEM1"
VERSION = (1).to_bytes(2, 'big')

# 64 MB per chunk - safe for memory even on large files
CHUNK_SIZE = 64 * 1024 * 1024


def derive_key(password: str, salt: bytes) -> bytes:
    """Turn a plain password into a strong 256-bit AES key using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,          # 256 bits
        salt=salt,
        iterations=600000,  # makes brute-force very slow
    )
    return kdf.derive(password.encode('utf-8'))


def _chunk_nonce(base_nonce: bytes, chunk_index: int) -> bytes:
    """XOR base nonce with chunk index so every chunk has a unique nonce."""
    index_bytes = chunk_index.to_bytes(12, 'big')
    return bytes(a ^ b for a, b in zip(base_nonce, index_bytes))


def encrypt_file(
    input_path: str,
    output_path: str,
    password: str,
    owner: str,
    progress_callback=None
) -> bool:
    """
    Encrypt any file and save it as a .dem file.
    Returns True on success, False on failure.
    Calls progress_callback(0.0 to 1.0) as it goes.
    """
    try:
        file_size = os.path.getsize(input_path)
        original_filename = os.path.basename(input_path)

        # Generate random salt and nonce (unique every time)
        salt = secrets.token_bytes(32)
        base_nonce = secrets.token_bytes(12)
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)

        # How many 64MB chunks will we need?
        num_chunks = max(1, (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE)

        owner_bytes = owner.encode('utf-8')
        filename_bytes = original_filename.encode('utf-8')

        with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:

            # ── Fixed header ──────────────────────────────────────────────
            fout.write(MAGIC)                                # 4 bytes  - file type
            fout.write(VERSION)                              # 2 bytes  - format version
            fout.write(salt)                                 # 32 bytes - key derivation salt
            fout.write(base_nonce)                           # 12 bytes - base nonce
            fout.write(num_chunks.to_bytes(4, 'big'))        # 4 bytes  - total chunks

            # ── Variable header ───────────────────────────────────────────
            fout.write(len(owner_bytes).to_bytes(2, 'big'))  # 2 bytes  - owner name length
            fout.write(owner_bytes)                          # variable - owner username
            fout.write(len(filename_bytes).to_bytes(2, 'big'))  # 2 bytes
            fout.write(filename_bytes)                       # variable - original filename
            fout.write(file_size.to_bytes(8, 'big'))         # 8 bytes  - original size

            # ── Encrypted chunks ──────────────────────────────────────────
            chunk_index = 0
            bytes_processed = 0

            while True:
                chunk = fin.read(CHUNK_SIZE)
                if not chunk:
                    break

                nonce = _chunk_nonce(base_nonce, chunk_index)
                encrypted_chunk = aesgcm.encrypt(nonce, chunk, None)

                fout.write(len(encrypted_chunk).to_bytes(4, 'big'))
                fout.write(encrypted_chunk)

                bytes_processed += len(chunk)
                chunk_index += 1

                if progress_callback and file_size > 0:
                    progress_callback(bytes_processed / file_size)

        if progress_callback:
            progress_callback(1.0)

        return True

    except Exception as e:
        print(f"[Encryption error] {e}")
        # Clean up partial output if something went wrong
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def decrypt_file(
    input_path: str,
    output_path: str,
    password: str,
    requesting_user: str,
    is_admin: bool = False,
    progress_callback=None
) -> tuple:
    """
    Decrypt a .dem file.
    Returns (True, owner_name)  on success.
    Returns (False, error_msg)  on failure.
    """
    try:
        with open(input_path, 'rb') as fin:

            # ── Read fixed header ─────────────────────────────────────────
            magic = fin.read(4)
            if magic != MAGIC:
                return False, "This is not a valid .dem file."

            _version = fin.read(2)
            salt = fin.read(32)
            base_nonce = fin.read(12)
            num_chunks = int.from_bytes(fin.read(4), 'big')

            # ── Read variable header ──────────────────────────────────────
            owner_len = int.from_bytes(fin.read(2), 'big')
            owner = fin.read(owner_len).decode('utf-8')

            filename_len = int.from_bytes(fin.read(2), 'big')
            original_filename = fin.read(filename_len).decode('utf-8')  # noqa: F841

            _original_size = int.from_bytes(fin.read(8), 'big')

            # ── Ownership check ───────────────────────────────────────────
            # Admins can decrypt any file. Users only their own.
            if not is_admin and requesting_user != owner:
                return False, (
                    f"Access denied. This file belongs to '{owner}'. "
                    "Only that user or an admin can decrypt it."
                )

            # ── Derive key and decrypt chunks ─────────────────────────────
            key = derive_key(password, salt)
            aesgcm = AESGCM(key)

            with open(output_path, 'wb') as fout:
                for chunk_index in range(num_chunks):
                    chunk_len = int.from_bytes(fin.read(4), 'big')
                    encrypted_chunk = fin.read(chunk_len)

                    nonce = _chunk_nonce(base_nonce, chunk_index)

                    try:
                        plaintext = aesgcm.decrypt(nonce, encrypted_chunk, None)
                    except Exception:
                        # Wrong password or corrupted file
                        return False, "Wrong password or the file is corrupted."

                    fout.write(plaintext)

                    if progress_callback:
                        progress_callback((chunk_index + 1) / num_chunks)

        return True, owner

    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return False, str(e)


def read_dem_header(input_path: str) -> dict | None:
    """
    Read only the header of a .dem file (no decryption).
    Useful for showing file info before the user enters a password.
    Returns a dict or None if the file is not a valid .dem file.
    """
    try:
        with open(input_path, 'rb') as f:
            magic = f.read(4)
            if magic != MAGIC:
                return None

            version = int.from_bytes(f.read(2), 'big')
            f.read(32)  # salt
            f.read(12)  # base_nonce
            num_chunks = int.from_bytes(f.read(4), 'big')

            owner_len = int.from_bytes(f.read(2), 'big')
            owner = f.read(owner_len).decode('utf-8')

            filename_len = int.from_bytes(f.read(2), 'big')
            original_filename = f.read(filename_len).decode('utf-8')

            original_size = int.from_bytes(f.read(8), 'big')

            return {
                'version': version,
                'owner': owner,
                'original_filename': original_filename,
                'original_size': original_size,
                'num_chunks': num_chunks,
            }
    except Exception:
        return None
