import os

import paramiko
import pytest

from kevinbotlib_deploytool.sshkeys import SSHKeyManager  # Assuming the original code is in ssh_key_manager.py


@pytest.fixture
def key_manager():
    """Fixture to initialize the SSHKeyManager and clean up after the test."""
    manager = SSHKeyManager(app_name="UnitTestingSSHKeys")
    yield manager
    # Cleanup: Remove all generated keys after the test
    key_info = manager._load_key_info()  # noqa: SLF001
    for private_key_path, public_key_path in key_info.values():
        if os.path.exists(private_key_path):
            os.remove(private_key_path)
        if os.path.exists(public_key_path):
            os.remove(public_key_path)
    # Optionally, remove the key_info file
    key_info_file = os.path.join(manager.key_dir, "key_info.pkl")
    if os.path.exists(key_info_file):
        os.remove(key_info_file)


def test_generate_key(key_manager):
    """Test generating and saving a key pair."""
    key_name = "test_key"
    private_key_path, public_key_path = key_manager.generate_key(key_name)

    # Ensure files exist
    assert os.path.exists(private_key_path)
    assert os.path.exists(public_key_path)

    # Ensure the private key is a valid RSA key
    private_key = paramiko.RSAKey(filename=private_key_path)
    assert private_key.get_bits() == 2048  # Check if it is a 2048-bit key

    # Ensure the public key has the correct format
    with open(public_key_path) as f:
        public_key = f.read().strip()
    assert public_key.startswith("ssh-rsa")

    # Clean up files after test
    os.remove(private_key_path)
    os.remove(public_key_path)


def test_remove_key(key_manager):
    """Test removing a key pair."""
    key_name = "key_to_remove"
    private_key_path, public_key_path = key_manager.generate_key(key_name)

    # Ensure files exist before removal
    assert os.path.exists(private_key_path)
    assert os.path.exists(public_key_path)

    # Remove the key
    key_manager.remove_key(key_name)

    # Ensure the files are removed
    assert not os.path.exists(private_key_path)
    assert not os.path.exists(public_key_path)


def test_list_keys(key_manager):
    """Test listing the saved keys."""
    key_name1 = "key1"
    key_name2 = "key2"
    key_manager.generate_key(key_name1)
    key_manager.generate_key(key_name2)

    # List keys and ensure both are present
    keys = key_manager.list_keys()
    assert key_name1 in keys
    assert key_name2 in keys

    # Clean up
    assert key_manager.remove_key(key_name1)
    assert key_manager.remove_key(key_name2)

    assert not key_manager.remove_key(key_name2)


def test_key_info_after_generate(key_manager):
    """Test that key information is correctly saved after generation."""
    key_name = "key_info_check"
    private_key_path, public_key_path = key_manager.generate_key(key_name)

    # Ensure the key information file exists and contains the expected data
    key_info = key_manager._load_key_info()  # noqa: SLF001
    assert key_name in key_info
    assert key_info[key_name] == [private_key_path, public_key_path]

    # Clean up
    key_manager.remove_key(key_name)
