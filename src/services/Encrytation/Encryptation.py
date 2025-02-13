from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64decode, b64encode
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from os import urandom
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptationService:

    def decrypt_request(self, body: dict, private_pem: str, passphrase: str) -> dict:
        def add_padding(b64_string):
            return b64_string + '=' * (-len(b64_string) % 4)

        # Debugging output
        print("Encrypted AES Key:", body['encrypted_aes_key'])
        print("Encrypted Flow Data:", body['encrypted_flow_data'])
        print("Initial Vector:", body['initial_vector'])

        encrypted_aes_key = b64decode(add_padding(body['encrypted_aes_key']))
        encrypted_flow_data = b64decode(add_padding(body['encrypted_flow_data']))
        initial_vector = b64decode(add_padding(body['initial_vector']))

        # Load private key
        private_key = serialization.load_pem_private_key(
            private_pem.encode(),
            password=passphrase.encode()
        )

        # Decrypt AES key using RSA
        try:
            decrypted_aes_key = private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            print(f"RSA Decryption Error: {e}")
            raise ValueError("Failed to decrypt the request. Please verify your private key.")

        # Split flow data into body and tag
        TAG_LENGTH = 16
        encrypted_flow_data_body = encrypted_flow_data[:-TAG_LENGTH]
        encrypted_flow_data_tag = encrypted_flow_data[-TAG_LENGTH:]

        # Decrypt flow data using AES-GCM
        cipher = Cipher(
            algorithms.AES(decrypted_aes_key),
            modes.GCM(initial_vector, encrypted_flow_data_tag)
        )
        decryptor = cipher.decryptor()

        try:
            decrypted_json_str = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
            decrypted_body = json.loads(decrypted_json_str.decode('utf-8'))
        except Exception as e:
            print(f"AES Decryption Error: {e}")
            raise ValueError("Failed to decrypt flow data. Please verify your AES key and IV.")

        return {
            'decryptedBody': decrypted_body,
            'aesKeyBuffer': decrypted_aes_key,
            'initialVectorBuffer': initial_vector
        }

    def encrypt_response(self, response: dict, aes_key_buffer: bytes, initial_vector_buffer: bytes) -> str:
        # Flip initial vector
        flipped_iv = bytearray(~b for b in initial_vector_buffer)

        # Encrypt response data using AES-GCM
        cipher = Cipher(
            algorithms.AES(aes_key_buffer),
            modes.GCM(flipped_iv)
        )
        encryptor = cipher.encryptor()
        response_json = json.dumps(response).encode('utf-8')
        encrypted_data = encryptor.update(response_json) + encryptor.finalize()
        auth_tag = encryptor.tag

        # Concatenate encrypted data and auth tag
        encrypted_response = encrypted_data + auth_tag
        return b64encode(encrypted_response).decode('utf-8')

    def encrypt_password(self, password: str) -> str:
        # Generar un salt aleatorio
        salt = urandom(16)

        # Derivar una clave utilizando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        # Retornar el salt y la clave encriptada como un string codificado
        return base64.urlsafe_b64encode(salt + key).decode('utf-8')

    def validate_password(self, password: str, encrypted_password: str) -> bool:
        # Decodificar la contraseña encriptada
        decoded = base64.urlsafe_b64decode(encrypted_password.encode())
        salt = decoded[:16]
        stored_key = decoded[16:]

        # Derivar la clave usando el mismo salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        # Comparar la clave derivada con la clave almacenada
        return key == stored_key