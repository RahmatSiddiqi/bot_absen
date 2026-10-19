import os
import sys
import getpass
from core.crypto import save_secure_credentials, load_secure_credentials

def main():
    print("=" * 60)
    print(" 🔐 SETUP KREDENSIAL TERENKRIPSI E-KINERJA (WINDOWS DPAPI)")
    print("=" * 60)
    print("Fitur ini mengenkripsi Email & Password E-Kinerja Anda dengan")
    print("keamanan Windows DPAPI sehingga nilai aslinya TIDAK BISA DIBACA")
    print("oleh siapapun yang membuka file di komputer ini.\n")

    email = input("Masukkan Email / NIP E-Kinerja: ").strip()
    if not email:
        print("[ERROR] Email tidak boleh kosong!")
        return

    password = getpass.getpass("Masukkan Password E-Kinerja (karakter tidak akan muncul): ").strip()
    if not password:
        print("[ERROR] Password tidak boleh kosong!")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    enc_path = os.path.join(base_dir, "credentials.enc")

    try:
        save_secure_credentials(enc_path, email, password)
        # Test decryption
        test = load_secure_credentials(enc_path)
        if test.get("email") != email:
            raise RuntimeError("Verifikasi dekripsi gagal.")
        print(f"\n[SUKSES] Kredensial berhasil dienkripsi dan disimpan di: credentials.enc")
    except Exception as e:
        print(f"\n[GAGAL] Terjadi kesalahan saat mengenkripsi: {e}")
        return

    # Bersihkan email & password dari .env jika ada
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                if line.startswith("EKINERJA_EMAIL="):
                    new_lines.append("# EKINERJA_EMAIL telah dipindahkan ke credentials.enc (terenkripsi)\nEKINERJA_EMAIL=\n")
                elif line.startswith("EKINERJA_PASSWORD="):
                    new_lines.append("# EKINERJA_PASSWORD telah dipindahkan ke credentials.enc (terenkripsi)\nEKINERJA_PASSWORD=\n")
                else:
                    new_lines.append(line)
            
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("[INFO] Kredensial plaintext di file .env berhasil dibersihkan/dikosongkan.")
        except Exception as e:
            print(f"[WARNING] Gagal membersihkan .env: {e}")

    print("\n" + "=" * 60)
    print("✅ PENGAMANAN SELESAI!")
    print("Sekarang file .env tidak lagi menyimpan password Anda.")
    print("Siapapun yang membuka file credentials.enc hanya akan melihat kode acak.")
    print("=" * 60)

if __name__ == "__main__":
    main()
