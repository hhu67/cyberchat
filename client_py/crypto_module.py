import os
import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Ensure the keys directory exists
KEYS_DIR = "keys"
os.makedirs(KEYS_DIR, exist_ok=True)

# Key file paths
PRIVATE_KEY_FILE = os.path.join(KEYS_DIR, "private_key.pem")
PUBLIC_KEY_FILE = os.path.join(KEYS_DIR, "public_key.pem")

def load_or_generate_keys():
    """
    Load existing keys or generate new Ed25519 keypair if none exist.
    """
    private_key = None
    public_key = None

    # Check if private key exists
    if os.path.exists(PRIVATE_KEY_FILE):
        with open(PRIVATE_KEY_FILE, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        
        # Load corresponding public key
        with open(PUBLIC_KEY_FILE, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
            )
    else:
        # Generate new keypair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Save private key
        with open(PRIVATE_KEY_FILE, "wb") as key_file:
            key_file.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Save public key
        with open(PUBLIC_KEY_FILE, "wb") as key_file:
            key_file.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

    return private_key, public_key


def sign_data(private_key, data):
    """
    Sign data using the private key.
    
    Args:
        private_key: Private key for signing.
        data: Data to sign (bytes).
    
    Returns:
        Signature as bytes.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    
    signature = private_key.sign(data)
    return signature


def verify_signature(public_key, signature, data):
    """
    Verify the signature of the data using the public key.
    
    Args:
        public_key: Public key for verification.
        signature: Signature to verify.
        data: Original data (bytes).
    
    Returns:
        True if the signature is valid, False otherwise.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    
    try:
        public_key.verify(signature, data)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # Example usage
    private_key, public_key = load_or_generate_keys()
    
    # Sign and verify example
    data = "Hello, world!"
    signature = sign_data(private_key, data)
    is_valid = verify_signature(public_key, signature, data)
    
    print(f"Signature valid: {is_valid}")