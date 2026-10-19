import sys
import json
import base64
import ctypes
import ctypes.wintypes

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def encrypt_data(plain_str: str) -> str:
    """Encrypt a string using Windows DPAPI (tied to current Windows User)."""
    if sys.platform != "win32":
        raise OSError("Windows DPAPI hanya tersedia di sistem operasi Windows.")
    
    data_bytes = plain_str.encode('utf-8')
    in_blob = DATA_BLOB(len(data_bytes), ctypes.cast(ctypes.create_string_buffer(data_bytes), ctypes.POINTER(ctypes.c_char)))
    out_blob = DATA_BLOB()
    
    # CryptProtectData: flags=0 (tied to current logged in Windows user)
    success = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        'EkinerjaSecret',
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob)
    )
    if not success:
        raise RuntimeError("Gagal melakukan enkripsi DPAPI Windows.")
    
    encrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return base64.b64encode(encrypted_bytes).decode('ascii')

def decrypt_data(enc_b64: str) -> str:
    """Decrypt a DPAPI encrypted base64 string on the same Windows User account."""
    if sys.platform != "win32":
        raise OSError("Windows DPAPI hanya tersedia di sistem operasi Windows.")
    
    enc_bytes = base64.b64decode(enc_b64)
    in_blob = DATA_BLOB(len(enc_bytes), ctypes.cast(ctypes.create_string_buffer(enc_bytes), ctypes.POINTER(ctypes.c_char)))
    out_blob = DATA_BLOB()
    
    success = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob)
    )
    if not success:
        raise RuntimeError("Gagal mendekripsi data. Pastikan dijalankan di akun Windows yang sama saat mengenkripsi.")
    
    decrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    return decrypted_bytes.decode('utf-8')

def save_secure_credentials(filepath: str, email: str, password: str):
    """Encrypt email & password and save to a secure binary/base64 file."""
    payload = json.dumps({"email": email, "password": password})
    encrypted_str = encrypt_data(payload)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(encrypted_str)

def load_secure_credentials(filepath: str) -> dict:
    """Load and decrypt credentials from file. Returns {'email': ..., 'password': ...}."""
    with open(filepath, "r", encoding="utf-8") as f:
        encrypted_str = f.read().strip()
    plain_json = decrypt_data(encrypted_str)
    return json.loads(plain_json)
