# flake8: noqa: F401
"""
Commands module.
Contains all start-commands, subcommands and CLI Interface creation.

Note: Be careful with file-scoped imports in these subfiles.
    as they are parsed on startup, nothing containing optional modules should be loaded.
"""
from coingro.commands.analyze_commands import start_analysis_entries_exits
from coingro.commands.arguments import Arguments
from coingro.commands.build_config_commands import start_new_config
from coingro.commands.data_commands import (
    start_convert_data,
    start_convert_trades,
    start_download_data,
    start_list_data,
)
from coingro.commands.db_commands import start_convert_db
from coingro.commands.deploy_commands import (
    start_create_userdir,
    start_install_ui,
    start_new_strategy,
)
from coingro.commands.hyperopt_commands import start_hyperopt_list, start_hyperopt_show
from coingro.commands.list_commands import (
    start_list_exchanges,
    start_list_markets,
    start_list_strategies,
    start_list_timeframes,
    start_show_trades,
)
from coingro.commands.optimize_commands import (
    start_backtesting,
    start_backtesting_show,
    start_edge,
    start_hyperopt,
)
from coingro.commands.pairlist_commands import start_test_pairlist
from coingro.commands.plot_commands import start_plot_dataframe, start_plot_profit
from coingro.commands.trade_commands import start_trading
from coingro.commands.webserver_commands import start_webserver
