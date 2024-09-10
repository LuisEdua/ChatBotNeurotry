from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64decode, b64encode
import json
import binascii


class EncryptationService:

    def decrypt_request(self, body: dict, private_pem: str, passphrase: str) -> dict:
        encrypted_aes_key = b64decode(body['encrypted_aes_key'])
        encrypted_flow_data = b64decode(body['encrypted_flow_data'])
        initial_vector = b64decode(body['initial_vector'])

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
            print(e)
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

        decrypted_json_str = decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
        decrypted_body = json.loads(decrypted_json_str.decode('utf-8'))

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


# Example usage
private_key_pem = """-----BEGIN ENCRYPTED PRIVATE KEY-----
...
-----END ENCRYPTED PRIVATE KEY-----"""
passphrase = "your_passphrase"

body = {
    "encrypted_aes_key": "base64_encoded_aes_key",
    "encrypted_flow_data": "base64_encoded_flow_data",
    "initial_vector": "base64_encoded_initial_vector"
}

service = EncryptationService()
decrypted_data = service.decrypt_request(body, private_key_pem, passphrase)
print(decrypted_data)

response = {"key": "value"}
encrypted_response = service.encrypt_response(response, decrypted_data['aesKeyBuffer'],
                                              decrypted_data['initialVectorBuffer'])
print(encrypted_response)
