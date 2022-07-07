"""
Utility function for Coingro security
"""
import base64
import logging
import os
import random
from copy import deepcopy
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from coingro import __id__
from coingro.constants import PROTECTED_CREDENTIALS
from coingro.exceptions import OperationalException
from coingro.misc import deep_merge_dicts


logger = logging.getLogger(__name__)


class Encryption:
    """
    Class for securing configuration files.
    """

    def __init__(self, config: Dict[str, Any] = {}) -> None:
        """
        Init all required variables
        """
        self.encrypted_config = {}
        self.plain_config = {}

        # Password could be further obfuscated
        self.__password = Encryption.shuffle(__id__.lower()).encode()

        if config.get('encryption', False):
            self.encrypted_config = config
            salt = config.get('salt')
            if isinstance(salt, bytes):
                self.salt = base64.decodebytes(salt)
            elif isinstance(salt, str):
                self.salt = base64.decodebytes(salt.encode())
            else:
                raise OperationalException('Config with encrypted credentials '
                                           'must contain a valid salt. ')
        else:
            self.plain_config = config
            self.salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=390000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.__password))
        self.cipher = Fernet(key)

    def get_encrypted_config(self) -> Dict[str, Any]:
        if not self.encrypted_config:
            self.encrypted_config = self._encrypt_config(deepcopy(self.plain_config),
                                                         PROTECTED_CREDENTIALS)
            self.encrypted_config.update({'encryption': True,
                                          'salt': base64.encodebytes(self.salt)})

        return self.encrypted_config

    def get_plain_config(self) -> Dict[str, Any]:
        if not self.plain_config:
            self.plain_config = self._decrypt_config(deepcopy(self.encrypted_config),
                                                     PROTECTED_CREDENTIALS)
            self.plain_config.update({'encryption': False, 'salt': None})
            self.plain_config.pop('salt')

        return self.plain_config

    def _encrypt_config(self, config: Dict[str, Any],
                        credentials: Optional[Dict[str, Optional[dict]]]) -> Dict[str, Any]:
        if credentials:
            for key in credentials:
                if credentials[key]:
                    sub_conf = config.get(key, {})
                    if sub_conf:
                        encrypted_sub_conf = self._encrypt_config(sub_conf, credentials[key])
                        deep_merge_dicts({key: encrypted_sub_conf}, config)
                else:
                    val = config.get(key, '')
                    if not isinstance(val, str):
                        raise OperationalException(f'{key} is not a string and '
                                                   'cannot be encrypted. ')
                    if val:
                        config[key] = self.encrypt(val)

        return config

    def _decrypt_config(self, config: Dict[str, Any],
                        credentials: Optional[Dict[str, Optional[dict]]]) -> Dict[str, Any]:
        if credentials:
            for key in credentials:
                if credentials[key]:
                    sub_conf = config.get(key, {})
                    if sub_conf:
                        decrypted_sub_conf = self._decrypt_config(sub_conf, credentials[key])
                        deep_merge_dicts({key: decrypted_sub_conf}, config)
                else:
                    val = config.get(key, '')
                    if not isinstance(val, str):
                        raise OperationalException(f'{key} is not a string and '
                                                   'cannot be decrypted. ')
                    if val:
                        config[key] = self.decrypt(val)

        return config

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def shuffle(word: str) -> str:
        lst = list(word)
        random.Random(len(word) * 16).shuffle(lst)
        return ''.join(lst)
