"""
This module contain functions to save the configuration file
"""
import logging
from pathlib import Path
from typing import Any, Dict

from coingro.configuration.config_security import Encryption
from coingro.constants import DEFAULT_CONFIG_SAVE, USERPATH_CONFIG
from coingro.misc import file_dump_json


logger = logging.getLogger(__name__)


def save_to_config_file(config: Dict[str, Any]):
    file_path = Path(config['user_data_dir']) / USERPATH_CONFIG / DEFAULT_CONFIG_SAVE

    if config.get('max_open_trades') == float('inf'):
        config['max_open_trades'] = -1

    config = Encryption(config).get_encrypted_config()
    file_dump_json(file_path, config, pretty_print=True, nan=True)

    logger.info('Config backup complete. ')
