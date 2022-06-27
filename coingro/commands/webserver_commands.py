from typing import Any, Dict

from coingro.enums import RunMode


def start_webserver(args: Dict[str, Any]) -> None:
    """
    Main entry point for webserver mode
    """
    from coingro.configuration import Configuration
    from coingro.rpc.api_server import ApiServer

    # Initialize configuration
    config = Configuration(args, RunMode.WEBSERVER).get_config()
    ApiServer(config, standalone=True)
