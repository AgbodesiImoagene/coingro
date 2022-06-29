"""
This module contain functions to save the configuration file
"""
import logging
from pathlib import Path
from typing import Any, Dict

from coingro.constants import DEFAULT_CONFIG_SAVE, USERPATH_CONFIG
from coingro.misc import file_dump_json


logger = logging.getLogger(__name__)


def save_to_config_file(config: Dict[str, Any]):
    file_path = Path(config['user_data_dir']) / USERPATH_CONFIG / DEFAULT_CONFIG_SAVE
    file_dump_json(file_path, config, pretty_print=True, nan=True)
