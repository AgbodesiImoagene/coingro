import logging
from pathlib import Path
from typing import Any, Dict

from coingro.configuration import setup_utils_configuration
from coingro.enums import RunMode
from coingro.exceptions import OperationalException

logger = logging.getLogger(__name__)


def setup_analyze_configuration(args: Dict[str, Any], method: RunMode) -> Dict[str, Any]:
    """
    Prepare the configuration for the entry/exit reason analysis module
    :param args: Cli args from Arguments()
    :param method: Bot running mode
    :return: Configuration
    """
    config = setup_utils_configuration(args, method)

    no_unlimited_runmodes = {
        RunMode.BACKTEST: "backtesting",
    }
    if method in no_unlimited_runmodes.keys():
        from coingro.data.btanalysis import get_latest_backtest_filename

        if "exportfilename" in config:
            if config["exportfilename"].is_dir():
                btfile = Path(get_latest_backtest_filename(config["exportfilename"]))
                signals_file = f"{config['exportfilename']}/{btfile.stem}_signals.pkl"
            else:
                if config["exportfilename"].exists():
                    btfile = Path(config["exportfilename"])
                    signals_file = f"{btfile.parent}/{btfile.stem}_signals.pkl"
                else:
                    raise OperationalException(f"{config['exportfilename']} does not exist.")
        else:
            raise OperationalException("exportfilename not in config.")

        if not Path(signals_file).exists():
            raise OperationalException(
                (
                    f"Cannot find latest backtest signals file: {signals_file}."
                    "Run backtesting with `--export signals`."
                )
            )

    return config


def start_analysis_entries_exits(args: Dict[str, Any]) -> None:
    """
    Start analysis script
    :param args: Cli args from Arguments()
    :return: None
    """
    from coingro.data.entryexitanalysis import process_entry_exit_reasons

    # Initialize configuration
    config = setup_analyze_configuration(args, RunMode.BACKTEST)

    logger.info("Starting coingro in analysis mode")

    process_entry_exit_reasons(
        config["exportfilename"],
        config["exchange"]["pair_whitelist"],
        config["analysis_groups"],
        config["enter_reason_list"],
        config["exit_reason_list"],
        config["indicator_list"],
    )
