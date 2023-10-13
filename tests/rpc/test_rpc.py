# pragma pylint: disable=missing-docstring, C0103
# pragma pylint: disable=invalid-sequence-index, invalid-name, too-many-arguments

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, MagicMock, PropertyMock

import pytest
from numpy import isnan

from coingro.edge import PairInfo
from coingro.enums import RunMode, SignalDirection, State, TradingMode
from coingro.exceptions import ExchangeError, InvalidOrderException, TemporaryError
from coingro.persistence import Trade
from coingro.persistence.pairlock_middleware import PairLocks
from coingro.rpc import RPC, RPCException
from coingro.rpc.fiat_convert import CryptoToFiatConverter
from tests.conftest import (
    CURRENT_TEST_STRATEGY,
    create_mock_trades,
    create_mock_trades_usdt,
    get_patched_coingrobot,
    patch_get_signal,
)


# Functions for recurrent object patching
def prec_satoshi(a, b) -> float:
    """
    :return: True if A and B differs less than one satoshi.
    """
    return abs(a - b) < 0.00000001


# Unit tests
def test_rpc_trade_status(default_conf, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    coingrobot.state = State.RUNNING
    with pytest.raises(RPCException, match=r".*no active trade*"):
        rpc._rpc_trade_status()

    coingrobot.enter_positions()
    trades = Trade.get_open_trades()
    trades[0].open_order_id = None
    coingrobot.exit_positions(trades)

    results = rpc._rpc_trade_status()
    assert results[0] == {
        "trade_id": 1,
        "pair": "ETH/BTC",
        "base_currency": "ETH",
        "quote_currency": "BTC",
        "open_date": ANY,
        "open_timestamp": ANY,
        "is_open": ANY,
        "fee_open": ANY,
        "fee_open_cost": ANY,
        "fee_open_currency": ANY,
        "fee_close": fee.return_value,
        "fee_close_cost": ANY,
        "fee_close_currency": ANY,
        "open_rate_requested": ANY,
        "open_trade_value": 0.0010025,
        "close_rate_requested": ANY,
        "sell_reason": ANY,
        "exit_reason": ANY,
        "exit_order_status": ANY,
        "min_rate": ANY,
        "max_rate": ANY,
        "strategy": ANY,
        "buy_tag": ANY,
        "enter_tag": ANY,
        "timeframe": 5,
        "open_order_id": ANY,
        "close_date": None,
        "close_timestamp": None,
        "open_rate": 1.098e-05,
        "close_rate": None,
        "current_rate": 1.099e-05,
        "amount": 91.07468123,
        "amount_requested": 91.07468124,
        "stake_amount": 0.001,
        "trade_duration": None,
        "trade_duration_s": None,
        "close_profit": None,
        "close_profit_pct": None,
        "close_profit_abs": None,
        "current_profit": -0.00408133,
        "current_profit_pct": -0.41,
        "current_profit_abs": -4.09e-06,
        "profit_ratio": -0.00408133,
        "profit_pct": -0.41,
        "profit_abs": -4.09e-06,
        "profit_fiat": ANY,
        "stop_loss_abs": 9.882e-06,
        "stop_loss_pct": -10.0,
        "stop_loss_ratio": -0.1,
        "stoploss_order_id": None,
        "stoploss_last_update": ANY,
        "stoploss_last_update_timestamp": ANY,
        "initial_stop_loss_abs": 9.882e-06,
        "initial_stop_loss_pct": -10.0,
        "initial_stop_loss_ratio": -0.1,
        "stoploss_current_dist": -1.1080000000000002e-06,
        "stoploss_current_dist_ratio": -0.10081893,
        "stoploss_current_dist_pct": -10.08,
        "stoploss_entry_dist": -0.00010475,
        "stoploss_entry_dist_ratio": -0.10448878,
        "open_order": None,
        "exchange": "binance",
        "leverage": 1.0,
        "interest_rate": 0.0,
        "liquidation_price": None,
        "is_short": False,
        "funding_fees": 0.0,
        "trading_mode": TradingMode.SPOT,
        "orders": [
            {
                "amount": 91.07468123,
                "average": 1.098e-05,
                "safe_price": 1.098e-05,
                "cost": 0.0009999999999054,
                "filled": 91.07468123,
                "cg_order_side": "buy",
                "order_date": ANY,
                "order_timestamp": ANY,
                "order_filled_date": ANY,
                "order_filled_timestamp": ANY,
                "order_type": "limit",
                "price": 1.098e-05,
                "is_open": False,
                "pair": "ETH/BTC",
                "order_id": ANY,
                "remaining": ANY,
                "status": ANY,
                "cg_is_entry": True,
            }
        ],
    }

    mocker.patch(
        "coingro.exchange.Exchange.get_rate",
        MagicMock(side_effect=ExchangeError("Pair 'ETH/BTC' not available")),
    )
    results = rpc._rpc_trade_status()
    assert isnan(results[0]["current_profit"])
    assert isnan(results[0]["current_rate"])
    assert results[0] == {
        "trade_id": 1,
        "pair": "ETH/BTC",
        "base_currency": "ETH",
        "quote_currency": "BTC",
        "open_date": ANY,
        "open_timestamp": ANY,
        "is_open": ANY,
        "fee_open": ANY,
        "fee_open_cost": ANY,
        "fee_open_currency": ANY,
        "fee_close": fee.return_value,
        "fee_close_cost": ANY,
        "fee_close_currency": ANY,
        "open_rate_requested": ANY,
        "open_trade_value": ANY,
        "close_rate_requested": ANY,
        "sell_reason": ANY,
        "exit_reason": ANY,
        "exit_order_status": ANY,
        "min_rate": ANY,
        "max_rate": ANY,
        "strategy": ANY,
        "buy_tag": ANY,
        "enter_tag": ANY,
        "timeframe": ANY,
        "open_order_id": ANY,
        "close_date": None,
        "close_timestamp": None,
        "open_rate": 1.098e-05,
        "close_rate": None,
        "current_rate": ANY,
        "amount": 91.07468123,
        "amount_requested": 91.07468124,
        "trade_duration": ANY,
        "trade_duration_s": ANY,
        "stake_amount": 0.001,
        "close_profit": None,
        "close_profit_pct": None,
        "close_profit_abs": None,
        "current_profit": ANY,
        "current_profit_pct": ANY,
        "current_profit_abs": ANY,
        "profit_ratio": ANY,
        "profit_pct": ANY,
        "profit_abs": ANY,
        "profit_fiat": ANY,
        "stop_loss_abs": 9.882e-06,
        "stop_loss_pct": -10.0,
        "stop_loss_ratio": -0.1,
        "stoploss_order_id": None,
        "stoploss_last_update": ANY,
        "stoploss_last_update_timestamp": ANY,
        "initial_stop_loss_abs": 9.882e-06,
        "initial_stop_loss_pct": -10.0,
        "initial_stop_loss_ratio": -0.1,
        "stoploss_current_dist": ANY,
        "stoploss_current_dist_ratio": ANY,
        "stoploss_current_dist_pct": ANY,
        "stoploss_entry_dist": -0.00010475,
        "stoploss_entry_dist_ratio": -0.10448878,
        "open_order": None,
        "exchange": "binance",
        "leverage": 1.0,
        "interest_rate": 0.0,
        "liquidation_price": None,
        "is_short": False,
        "funding_fees": 0.0,
        "trading_mode": TradingMode.SPOT,
        "orders": [
            {
                "amount": 91.07468123,
                "average": 1.098e-05,
                "safe_price": 1.098e-05,
                "cost": 0.0009999999999054,
                "filled": 91.07468123,
                "cg_order_side": "buy",
                "order_date": ANY,
                "order_timestamp": ANY,
                "order_filled_date": ANY,
                "order_filled_timestamp": ANY,
                "order_type": "limit",
                "price": 1.098e-05,
                "is_open": False,
                "pair": "ETH/BTC",
                "order_id": ANY,
                "remaining": ANY,
                "status": ANY,
                "cg_is_entry": True,
            }
        ],
    }


def test_rpc_status_table(default_conf, ticker, fee, mocker) -> None:
    mocker.patch.multiple(
        "coingro.rpc.fiat_convert.CoinGeckoAPI",
        get_price=MagicMock(return_value={"bitcoin": {"usd": 15000.0}}),
    )
    mocker.patch("coingro.rpc.rpc.CryptoToFiatConverter._find_price", return_value=15000.0)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        get_fee=fee,
    )
    del default_conf["fiat_display_currency"]
    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    coingrobot.state = State.RUNNING
    with pytest.raises(RPCException, match=r".*no active trade*"):
        rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    mocker.patch("coingro.exchange.Exchange._is_dry_limit_order_filled", return_value=False)
    coingrobot.enter_positions()

    result, headers, fiat_profit_sum = rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    assert "Since" in headers
    assert "Pair" in headers
    assert "instantly" == result[0][2]
    assert "ETH/BTC" in result[0][1]
    assert "0.00" == result[0][3]
    assert isnan(fiat_profit_sum)

    mocker.patch("coingro.exchange.Exchange._is_dry_limit_order_filled", return_value=True)
    coingrobot.process()

    result, headers, fiat_profit_sum = rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    assert "Since" in headers
    assert "Pair" in headers
    assert "instantly" == result[0][2]
    assert "ETH/BTC" in result[0][1]
    assert "-0.41%" == result[0][3]
    assert isnan(fiat_profit_sum)

    # Test with fiatconvert
    rpc._fiat_converter = CryptoToFiatConverter()
    result, headers, fiat_profit_sum = rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    assert "Since" in headers
    assert "Pair" in headers
    assert len(result[0]) == 4
    assert "instantly" == result[0][2]
    assert "ETH/BTC" in result[0][1]
    assert "-0.41% (-0.06)" == result[0][3]
    assert "-0.06" == f"{fiat_profit_sum:.2f}"

    rpc._config["position_adjustment_enable"] = True
    rpc._config["max_entry_position_adjustment"] = 3
    result, headers, fiat_profit_sum = rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    assert "# Entries" in headers
    assert len(result[0]) == 5
    # 4th column should be 1/4 - as 1 order filled (a total of 4 is possible)
    # 3 on top of the initial one.
    assert result[0][4] == "1/4"

    mocker.patch(
        "coingro.exchange.Exchange.get_rate",
        MagicMock(side_effect=ExchangeError("Pair 'ETH/BTC' not available")),
    )
    result, headers, fiat_profit_sum = rpc._rpc_status_table(default_conf["stake_currency"], "USD")
    assert "instantly" == result[0][2]
    assert "ETH/BTC" in result[0][1]
    assert "nan%" == result[0][3]
    assert isnan(fiat_profit_sum)


def test__rpc_timeunit_profit(
    default_conf_usdt, ticker, fee, limit_buy_order, limit_sell_order, markets, mocker
) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        get_fee=fee,
        markets=PropertyMock(return_value=markets),
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf_usdt)
    create_mock_trades_usdt(fee)

    stake_currency = default_conf_usdt["stake_currency"]
    fiat_display_currency = default_conf_usdt["fiat_display_currency"]

    rpc = RPC(coingrobot)
    rpc._fiat_converter = CryptoToFiatConverter()

    # Try valid data
    days = rpc._rpc_timeunit_profit(7, stake_currency, fiat_display_currency)
    assert len(days["data"]) == 7
    assert days["stake_currency"] == default_conf_usdt["stake_currency"]
    assert days["fiat_display_currency"] == default_conf_usdt["fiat_display_currency"]
    for day in days["data"]:
        # {'date': datetime.date(2022, 6, 11), 'abs_profit': 13.8299999,
        #  'starting_balance': 1055.37, 'rel_profit': 0.0131044,
        #  'fiat_value': 0.0, 'trade_count': 2}
        assert day["abs_profit"] in (0.0, pytest.approx(13.8299999), pytest.approx(-4.0))
        assert day["rel_profit"] in (0.0, pytest.approx(0.01310441), pytest.approx(-0.00377583))
        assert day["trade_count"] in (0, 1, 2)
        assert day["starting_balance"] in (pytest.approx(1059.37), pytest.approx(1055.37))
        assert day["fiat_value"] in (0.0,)
    # ensure first day is current date
    assert str(days["data"][0]["date"]) == str(datetime.utcnow().date())

    # Try invalid data
    with pytest.raises(RPCException, match=r".*must be an integer greater than 0*"):
        rpc._rpc_timeunit_profit(0, stake_currency, fiat_display_currency)


@pytest.mark.parametrize("is_short", [True, False])
def test_rpc_trade_history(mocker, default_conf, markets, fee, is_short):
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", markets=PropertyMock(return_value=markets))

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    create_mock_trades(fee, is_short)
    rpc = RPC(coingrobot)
    rpc._fiat_converter = CryptoToFiatConverter()
    trades = rpc._rpc_trade_history(2)
    assert len(trades["trades"]) == 2
    assert trades["trades_count"] == 2
    assert isinstance(trades["trades"][0], dict)
    assert isinstance(trades["trades"][1], dict)

    trades = rpc._rpc_trade_history(0)
    assert len(trades["trades"]) == 2
    assert trades["trades_count"] == 2
    # The first closed trade is for ETC ... sorting is descending
    assert trades["trades"][-1]["pair"] == "ETC/BTC"
    assert trades["trades"][0]["pair"] == "XRP/BTC"


@pytest.mark.parametrize("is_short", [True, False])
def test_rpc_delete_trade(mocker, default_conf, fee, markets, caplog, is_short):
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    stoploss_mock = MagicMock()
    cancel_mock = MagicMock()
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        markets=PropertyMock(return_value=markets),
        cancel_order=cancel_mock,
        cancel_stoploss_order=stoploss_mock,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    coingrobot.strategy.order_types["stoploss_on_exchange"] = True
    create_mock_trades(fee, is_short)
    rpc = RPC(coingrobot)
    with pytest.raises(RPCException, match="invalid argument"):
        rpc._rpc_delete("200")

    trades = Trade.query.all()
    trades[1].stoploss_order_id = "1234"
    trades[2].stoploss_order_id = "1234"
    assert len(trades) > 2

    res = rpc._rpc_delete("1")
    assert isinstance(res, dict)
    assert res["result"] == "success"
    assert res["trade_id"] == "1"
    assert res["cancel_order_count"] == 1
    assert cancel_mock.call_count == 1
    assert stoploss_mock.call_count == 0
    cancel_mock.reset_mock()
    stoploss_mock.reset_mock()

    res = rpc._rpc_delete("2")
    assert isinstance(res, dict)
    assert cancel_mock.call_count == 1
    assert stoploss_mock.call_count == 1
    assert res["cancel_order_count"] == 2

    stoploss_mock = mocker.patch(
        "coingro.exchange.Exchange.cancel_stoploss_order", side_effect=InvalidOrderException
    )

    res = rpc._rpc_delete("3")
    assert stoploss_mock.call_count == 1
    stoploss_mock.reset_mock()

    cancel_mock = mocker.patch(
        "coingro.exchange.Exchange.cancel_order", side_effect=InvalidOrderException
    )

    res = rpc._rpc_delete("4")
    assert cancel_mock.call_count == 1
    assert stoploss_mock.call_count == 0


def test_rpc_trade_statistics(default_conf_usdt, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.rpc.CryptoToFiatConverter._find_price", return_value=1.1)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf_usdt)
    stake_currency = default_conf_usdt["stake_currency"]
    fiat_display_currency = default_conf_usdt["fiat_display_currency"]

    rpc = RPC(coingrobot)
    rpc._fiat_converter = CryptoToFiatConverter()

    res = rpc._rpc_trade_statistics(stake_currency, fiat_display_currency)
    assert res["trade_count"] == 0
    assert res["first_trade_date"] == ""
    assert res["first_trade_timestamp"] == 0
    assert res["latest_trade_date"] == ""
    assert res["latest_trade_timestamp"] == 0

    # Create some test data
    create_mock_trades_usdt(fee)

    stats = rpc._rpc_trade_statistics(stake_currency, fiat_display_currency)
    assert pytest.approx(stats["profit_closed_coin"]) == 9.83
    assert pytest.approx(stats["profit_closed_percent_mean"]) == -1.67
    assert pytest.approx(stats["profit_closed_fiat"]) == 10.813
    assert pytest.approx(stats["profit_all_coin"]) == -77.45964918
    assert pytest.approx(stats["profit_all_percent_mean"]) == -57.86
    assert pytest.approx(stats["profit_all_fiat"]) == -85.205614098
    assert stats["trade_count"] == 7
    assert stats["first_trade_date"] == "2 days ago"
    assert stats["latest_trade_date"] == "17 minutes ago"
    assert stats["avg_duration"] in ("0:17:40")
    assert stats["best_pair"] == "XRP/USDT"
    assert stats["best_rate"] == 10.0

    # Test non-available pair
    mocker.patch(
        "coingro.exchange.Exchange.get_rate",
        MagicMock(side_effect=ExchangeError("Pair 'XRP/USDT' not available")),
    )
    stats = rpc._rpc_trade_statistics(stake_currency, fiat_display_currency)
    assert stats["trade_count"] == 7
    assert stats["first_trade_date"] == "2 days ago"
    assert stats["latest_trade_date"] == "17 minutes ago"
    assert stats["avg_duration"] in ("0:17:40")
    assert stats["best_pair"] == "XRP/USDT"
    assert stats["best_rate"] == 10.0
    assert isnan(stats["profit_all_coin"])


# Test that rpc_trade_statistics can handle trades that lacks
# trade.open_rate (it is set to None)
def test_rpc_trade_statistics_closed(mocker, default_conf_usdt, ticker, fee):
    mocker.patch("coingro.rpc.fiat_convert.CryptoToFiatConverter._find_price", return_value=1.1)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf_usdt)
    patch_get_signal(coingrobot)
    stake_currency = default_conf_usdt["stake_currency"]
    fiat_display_currency = default_conf_usdt["fiat_display_currency"]

    rpc = RPC(coingrobot)

    # Create some test data
    create_mock_trades_usdt(fee)

    for trade in Trade.query.order_by(Trade.id).all():
        trade.open_rate = None

    stats = rpc._rpc_trade_statistics(stake_currency, fiat_display_currency)
    assert stats["profit_closed_coin"] == 0
    assert stats["profit_closed_percent_mean"] == 0
    assert stats["profit_closed_fiat"] == 0
    assert stats["profit_all_coin"] == 0
    assert stats["profit_all_percent_mean"] == 0
    assert stats["profit_all_fiat"] == 0
    assert stats["trade_count"] == 7
    assert stats["first_trade_date"] == "2 days ago"
    assert stats["latest_trade_date"] == "17 minutes ago"
    assert stats["avg_duration"] == "0:00:00"
    assert stats["best_pair"] == "XRP/USDT"
    assert stats["best_rate"] == 10.0


def test_rpc_balance_handle_error(default_conf, mocker):
    mock_balance = {
        "BTC": {
            "free": 10.0,
            "total": 12.0,
            "used": 2.0,
        },
        "ETH": {
            "free": 1.0,
            "total": 5.0,
            "used": 4.0,
        },
    }
    # ETH will be skipped due to mocked Error below

    mocker.patch.multiple(
        "coingro.rpc.fiat_convert.CoinGeckoAPI",
        get_price=MagicMock(return_value={"bitcoin": {"usd": 15000.0}}),
    )
    mocker.patch("coingro.rpc.rpc.CryptoToFiatConverter._find_price", return_value=15000.0)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=mock_balance),
        get_tickers=MagicMock(side_effect=TemporaryError("Could not load ticker due to xxx")),
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    rpc._fiat_converter = CryptoToFiatConverter()
    with pytest.raises(RPCException, match="Error getting current tickers."):
        rpc._rpc_balance(default_conf["stake_currency"], default_conf["fiat_display_currency"])


def test_rpc_balance_handle(default_conf, mocker, tickers):
    mock_balance = {
        "BTC": {
            "free": 10.0,
            "total": 12.0,
            "used": 2.0,
        },
        "ETH": {
            "free": 1.0,
            "total": 5.0,
            "used": 4.0,
        },
        "USDT": {
            "free": 5.0,
            "total": 10.0,
            "used": 5.0,
        },
    }
    mock_pos = [
        {
            "symbol": "ETH/USDT:USDT",
            "timestamp": None,
            "datetime": None,
            "initialMargin": 0.0,
            "initialMarginPercentage": None,
            "maintenanceMargin": 0.0,
            "maintenanceMarginPercentage": 0.005,
            "entryPrice": 0.0,
            "notional": 100.0,
            "leverage": 5.0,
            "unrealizedPnl": 0.0,
            "contracts": 100.0,
            "contractSize": 1,
            "marginRatio": None,
            "liquidationPrice": 0.0,
            "markPrice": 2896.41,
            "collateral": 20,
            "marginType": "isolated",
            "side": "short",
            "percentage": None,
        }
    ]

    mocker.patch.multiple(
        "coingro.rpc.fiat_convert.CoinGeckoAPI",
        get_price=MagicMock(return_value={"bitcoin": {"usd": 15000.0}}),
    )
    mocker.patch("coingro.rpc.rpc.CryptoToFiatConverter._find_price", return_value=15000.0)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        validate_trading_mode_and_margin_mode=MagicMock(),
        get_balances=MagicMock(return_value=mock_balance),
        fetch_positions=MagicMock(return_value=mock_pos),
        get_tickers=tickers,
        get_valid_pair_combination=MagicMock(
            side_effect=lambda a, b: f"{b}/{a}" if a == "USDT" else f"{a}/{b}"
        ),
    )
    default_conf["dry_run"] = False
    default_conf["trading_mode"] = "futures"
    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    rpc._fiat_converter = CryptoToFiatConverter()

    result = rpc._rpc_balance(default_conf["stake_currency"], default_conf["fiat_display_currency"])
    assert prec_satoshi(result["total"], 30.30909624)
    assert prec_satoshi(result["value"], 454636.44360691)
    assert tickers.call_count == 1
    assert tickers.call_args_list[0][1]["cached"] is True
    assert "USD" == result["symbol"]
    assert result["currencies"] == [
        {
            "currency": "BTC",
            "free": 10.0,
            "balance": 12.0,
            "used": 2.0,
            "est_stake": 10.0,  # In futures mode, "free" is used here.
            "stake": "BTC",
            "is_position": False,
            "leverage": 1.0,
            "position": 0.0,
            "side": "long",
        },
        {
            "free": 1.0,
            "balance": 5.0,
            "currency": "ETH",
            "est_stake": 0.30794,
            "used": 4.0,
            "stake": "BTC",
            "is_position": False,
            "leverage": 1.0,
            "position": 0.0,
            "side": "long",
        },
        {
            "free": 5.0,
            "balance": 10.0,
            "currency": "USDT",
            "est_stake": 0.0011562404610161968,
            "used": 5.0,
            "stake": "BTC",
            "is_position": False,
            "leverage": 1.0,
            "position": 0.0,
            "side": "long",
        },
        {
            "free": 0.0,
            "balance": 0.0,
            "currency": "ETH/USDT:USDT",
            "est_stake": 20,
            "used": 0,
            "stake": "BTC",
            "is_position": True,
            "leverage": 5.0,
            "position": 1000.0,
            "side": "short",
        },
    ]


def test_rpc_start(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", fetch_ticker=MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    coingrobot.state = State.STOPPED

    result = rpc._rpc_start()
    assert {"status": "starting trader ..."} == result
    assert coingrobot.state == State.RUNNING

    result = rpc._rpc_start()
    assert {"status": "already running"} == result
    assert coingrobot.state == State.RUNNING


def test_rpc_stop(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", fetch_ticker=MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    coingrobot.state = State.RUNNING

    result = rpc._rpc_stop()
    assert {"status": "stopping trader ..."} == result
    assert coingrobot.state == State.STOPPED

    result = rpc._rpc_stop()

    assert {"status": "already stopped"} == result
    assert coingrobot.state == State.STOPPED


def test_rpc_stopbuy(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", fetch_ticker=MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    coingrobot.state = State.RUNNING

    assert coingrobot.config["max_open_trades"] != 0
    result = rpc._rpc_stopbuy()
    assert {"status": "No more buy will occur from now. Run /reload_config to reset."} == result
    assert coingrobot.config["max_open_trades"] == 0


def test_rpc_force_exit(default_conf, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    cancel_order_mock = MagicMock()
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        fetch_ticker=ticker,
        cancel_order=cancel_order_mock,
        fetch_order=MagicMock(
            return_value={
                "status": "closed",
                "type": "limit",
                "side": "buy",
                "filled": 0.0,
            }
        ),
        _is_dry_limit_order_filled=MagicMock(return_value=True),
        get_fee=fee,
    )
    mocker.patch("coingro.wallets.Wallets.get_free", return_value=1000)

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    coingrobot.state = State.STOPPED
    with pytest.raises(RPCException, match=r".*trader is not running*"):
        rpc._rpc_force_exit(None)

    coingrobot.state = State.RUNNING
    with pytest.raises(RPCException, match=r".*invalid argument*"):
        rpc._rpc_force_exit(None)

    msg = rpc._rpc_force_exit("all")
    assert msg == {"result": "Created sell orders for all open trades."}

    coingrobot.enter_positions()
    msg = rpc._rpc_force_exit("all")
    assert msg == {"result": "Created sell orders for all open trades."}

    coingrobot.enter_positions()
    msg = rpc._rpc_force_exit("2")
    assert msg == {"result": "Created sell order for trade 2."}

    coingrobot.state = State.STOPPED
    with pytest.raises(RPCException, match=r".*trader is not running*"):
        rpc._rpc_force_exit(None)

    with pytest.raises(RPCException, match=r".*trader is not running*"):
        rpc._rpc_force_exit("all")

    coingrobot.state = State.RUNNING
    assert cancel_order_mock.call_count == 0
    mocker.patch(
        "coingro.exchange.Exchange._is_dry_limit_order_filled", MagicMock(return_value=False)
    )
    coingrobot.enter_positions()
    # make an limit-buy open trade
    trade = Trade.query.filter(Trade.id == "3").first()
    filled_amount = trade.amount / 2
    # Fetch order - it's open first, and closed after cancel_order is called.
    mocker.patch(
        "coingro.exchange.Exchange.fetch_order",
        side_effect=[
            {
                "id": trade.orders[0].order_id,
                "status": "open",
                "type": "limit",
                "side": "buy",
                "filled": filled_amount,
            },
            {
                "id": trade.orders[0].order_id,
                "status": "closed",
                "type": "limit",
                "side": "buy",
                "filled": filled_amount,
            },
        ],
    )
    # check that the trade is called, which is done by ensuring exchange.cancel_order is called
    # and trade amount is updated
    rpc._rpc_force_exit("3")
    assert cancel_order_mock.call_count == 1
    assert trade.amount == filled_amount

    mocker.patch(
        "coingro.exchange.Exchange.fetch_order",
        return_value={"status": "open", "type": "limit", "side": "buy", "filled": filled_amount},
    )

    coingrobot.config["max_open_trades"] = 3
    coingrobot.enter_positions()
    trade = Trade.query.filter(Trade.id == "2").first()
    amount = trade.amount
    # make an limit-buy open trade, if there is no 'filled', don't sell it
    mocker.patch(
        "coingro.exchange.Exchange.fetch_order",
        return_value={"status": "open", "type": "limit", "side": "buy", "filled": None},
    )
    # check that the trade is called, which is done by ensuring exchange.cancel_order is called
    msg = rpc._rpc_force_exit("4")
    assert msg == {"result": "Created sell order for trade 4."}
    assert cancel_order_mock.call_count == 2
    assert trade.amount == amount

    # make an limit-sell open trade
    mocker.patch(
        "coingro.exchange.Exchange.fetch_order",
        return_value={
            "status": "open",
            "type": "limit",
            "side": "sell",
            "amount": amount,
            "remaining": amount,
            "filled": 0.0,
        },
    )
    msg = rpc._rpc_force_exit("3")
    assert msg == {"result": "Created sell order for trade 3."}
    # status quo, no exchange calls
    assert cancel_order_mock.call_count == 3


def test_performance_handle(default_conf_usdt, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf_usdt)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    # Create some test data
    create_mock_trades_usdt(fee)

    res = rpc._rpc_performance()
    assert len(res) == 3
    assert res[0]["pair"] == "XRP/USDT"
    assert res[0]["count"] == 1
    assert res[0]["profit_pct"] == 10.0


def test_enter_tag_performance_handle(default_conf, ticker, fee, mocker) -> None:

    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    # Create some test data
    create_mock_trades_usdt(fee)
    coingrobot.enter_positions()

    res = rpc._rpc_enter_tag_performance(None)

    assert len(res) == 3
    assert res[0]["enter_tag"] == "TEST3"
    assert res[0]["count"] == 1
    assert res[0]["profit_pct"] == 10.0

    res = rpc._rpc_enter_tag_performance(None)

    assert len(res) == 3
    assert res[0]["enter_tag"] == "TEST3"
    assert res[0]["count"] == 1
    assert res[0]["profit_pct"] == 10.0


def test_enter_tag_performance_handle_2(mocker, default_conf, markets, fee):
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", markets=PropertyMock(return_value=markets))

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    create_mock_trades(fee)
    rpc = RPC(coingrobot)

    res = rpc._rpc_enter_tag_performance(None)

    assert len(res) == 2
    assert res[0]["enter_tag"] == "TEST1"
    assert res[0]["count"] == 1
    assert prec_satoshi(res[0]["profit_pct"], 0.5)
    assert res[1]["enter_tag"] == "Other"
    assert res[1]["count"] == 1
    assert prec_satoshi(res[1]["profit_pct"], 1.0)

    # Test for a specific pair
    res = rpc._rpc_enter_tag_performance("ETC/BTC")
    assert len(res) == 1
    assert res[0]["count"] == 1
    assert res[0]["enter_tag"] == "TEST1"
    assert prec_satoshi(res[0]["profit_pct"], 0.5)


def test_exit_reason_performance_handle(default_conf_usdt, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf_usdt)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    # Create some test data
    create_mock_trades_usdt(fee)

    res = rpc._rpc_exit_reason_performance(None)

    assert len(res) == 3
    assert res[0]["exit_reason"] == "roi"
    assert res[0]["count"] == 1
    assert res[0]["profit_pct"] == 10.0

    assert res[1]["exit_reason"] == "exit_signal"
    assert res[2]["exit_reason"] == "Other"


def test_exit_reason_performance_handle_2(mocker, default_conf, markets, fee):
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", markets=PropertyMock(return_value=markets))

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    create_mock_trades(fee)
    rpc = RPC(coingrobot)

    res = rpc._rpc_exit_reason_performance(None)

    assert len(res) == 2
    assert res[0]["exit_reason"] == "sell_signal"
    assert res[0]["count"] == 1
    assert prec_satoshi(res[0]["profit_pct"], 0.5)
    assert res[1]["exit_reason"] == "roi"
    assert res[1]["count"] == 1
    assert prec_satoshi(res[1]["profit_pct"], 1.0)

    # Test for a specific pair
    res = rpc._rpc_exit_reason_performance("ETC/BTC")
    assert len(res) == 1
    assert res[0]["count"] == 1
    assert res[0]["exit_reason"] == "sell_signal"
    assert prec_satoshi(res[0]["profit_pct"], 0.5)


def test_mix_tag_performance_handle(default_conf, ticker, fee, mocker) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    # Create some test data
    create_mock_trades_usdt(fee)

    res = rpc._rpc_mix_tag_performance(None)

    assert len(res) == 3
    assert res[0]["mix_tag"] == "TEST3 roi"
    assert res[0]["count"] == 1
    assert res[0]["profit_pct"] == 10.0


def test_mix_tag_performance_handle_2(mocker, default_conf, markets, fee):
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple("coingro.exchange.Exchange", markets=PropertyMock(return_value=markets))

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    create_mock_trades(fee)
    rpc = RPC(coingrobot)

    res = rpc._rpc_mix_tag_performance(None)

    assert len(res) == 2
    assert res[0]["mix_tag"] == "TEST1 sell_signal"
    assert res[0]["count"] == 1
    assert prec_satoshi(res[0]["profit_pct"], 0.5)
    assert res[1]["mix_tag"] == "Other roi"
    assert res[1]["count"] == 1
    assert prec_satoshi(res[1]["profit_pct"], 1.0)

    # Test for a specific pair
    res = rpc._rpc_mix_tag_performance("ETC/BTC")

    assert len(res) == 1
    assert res[0]["count"] == 1
    assert res[0]["mix_tag"] == "TEST1 sell_signal"
    assert prec_satoshi(res[0]["profit_pct"], 0.5)


def test_rpc_count(mocker, default_conf, ticker, fee) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)

    counts = rpc._rpc_count()
    assert counts["current"] == 0

    # Create some test data
    coingrobot.enter_positions()
    counts = rpc._rpc_count()
    assert counts["current"] == 1


def test_rpc_force_entry(mocker, default_conf, ticker, fee, limit_buy_order_open) -> None:
    default_conf["force_entry_enable"] = True
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    buy_mm = MagicMock(return_value=limit_buy_order_open)
    mocker.patch.multiple(
        "coingro.exchange.Exchange",
        get_balances=MagicMock(return_value=ticker),
        fetch_ticker=ticker,
        get_fee=fee,
        create_order=buy_mm,
    )

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    pair = "ETH/BTC"
    trade = rpc._rpc_force_entry(pair, None)
    assert isinstance(trade, Trade)
    assert trade.pair == pair
    assert trade.open_rate == ticker()["bid"]

    # Test buy duplicate
    with pytest.raises(RPCException, match=r"position for ETH/BTC already open - id: 1"):
        rpc._rpc_force_entry(pair, 0.0001)
    pair = "XRP/BTC"
    trade = rpc._rpc_force_entry(pair, 0.0001, order_type="limit")
    assert isinstance(trade, Trade)
    assert trade.pair == pair
    assert trade.open_rate == 0.0001

    # Test buy pair not with stakes
    with pytest.raises(
        RPCException, match=r"Wrong pair selected. Only pairs with stake-currency.*"
    ):
        rpc._rpc_force_entry("LTC/ETH", 0.0001)

    # Test with defined stake_amount
    pair = "LTC/BTC"
    trade = rpc._rpc_force_entry(pair, 0.0001, order_type="limit", stake_amount=0.05)
    assert trade.stake_amount == 0.05
    assert trade.buy_tag == "force_entry"

    # Test not buying
    pair = "XRP/BTC"
    coingrobot = get_patched_coingrobot(mocker, default_conf)
    coingrobot.config["stake_amount"] = 0
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    pair = "TKN/BTC"
    with pytest.raises(RPCException, match=r"Failed to enter position for TKN/BTC."):
        trade = rpc._rpc_force_entry(pair, None)


def test_rpc_force_entry_stopped(mocker, default_conf) -> None:
    default_conf["force_entry_enable"] = True
    default_conf["initial_state"] = "stopped"
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    pair = "ETH/BTC"
    with pytest.raises(RPCException, match=r"trader is not running"):
        rpc._rpc_force_entry(pair, None)


def test_rpc_force_entry_disabled(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    pair = "ETH/BTC"
    with pytest.raises(RPCException, match=r"Force_entry not enabled."):
        rpc._rpc_force_entry(pair, None)


def test_rpc_force_entry_wrong_mode(mocker, default_conf) -> None:
    default_conf["force_entry_enable"] = True
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    patch_get_signal(coingrobot)
    rpc = RPC(coingrobot)
    pair = "ETH/BTC"
    with pytest.raises(RPCException, match="Can't go short on Spot markets."):
        rpc._rpc_force_entry(pair, None, order_side=SignalDirection.SHORT)


@pytest.mark.usefixtures("init_persistence")
def test_rpc_delete_lock(mocker, default_conf):
    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    pair = "ETH/BTC"

    PairLocks.lock_pair(pair, datetime.now(timezone.utc) + timedelta(minutes=4))
    PairLocks.lock_pair(pair, datetime.now(timezone.utc) + timedelta(minutes=5))
    PairLocks.lock_pair(pair, datetime.now(timezone.utc) + timedelta(minutes=10))
    locks = rpc._rpc_locks()
    assert locks["lock_count"] == 3
    locks1 = rpc._rpc_delete_lock(lockid=locks["locks"][0]["id"])
    assert locks1["lock_count"] == 2

    locks2 = rpc._rpc_delete_lock(pair=pair)
    assert locks2["lock_count"] == 0


def test_rpc_whitelist(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    ret = rpc._rpc_whitelist()
    assert len(ret["method"]) == 1
    assert "StaticPairList" in ret["method"]
    assert ret["whitelist"] == default_conf["exchange"]["pair_whitelist"]


def test_rpc_whitelist_dynamic(mocker, default_conf) -> None:
    default_conf["pairlists"] = [
        {
            "method": "VolumePairList",
            "number_assets": 4,
        }
    ]
    mocker.patch("coingro.exchange.Exchange.exchange_has", MagicMock(return_value=True))
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    ret = rpc._rpc_whitelist()
    assert len(ret["method"]) == 1
    assert "VolumePairList" in ret["method"]
    assert ret["length"] == 4
    assert ret["whitelist"] == default_conf["exchange"]["pair_whitelist"]


def test_rpc_blacklist(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    ret = rpc._rpc_blacklist(None)
    assert len(ret["method"]) == 1
    assert "StaticPairList" in ret["method"]
    assert len(ret["blacklist"]) == 2
    assert ret["blacklist"] == default_conf["exchange"]["pair_blacklist"]
    assert ret["blacklist"] == ["DOGE/BTC", "HOT/BTC"]

    ret = rpc._rpc_blacklist(["ETH/BTC"])
    assert "StaticPairList" in ret["method"]
    assert len(ret["blacklist"]) == 3
    assert ret["blacklist"] == default_conf["exchange"]["pair_blacklist"]
    assert ret["blacklist"] == ["DOGE/BTC", "HOT/BTC", "ETH/BTC"]

    ret = rpc._rpc_blacklist(["ETH/BTC"])
    assert "errors" in ret
    assert isinstance(ret["errors"], dict)
    assert ret["errors"]["ETH/BTC"]["error_msg"] == "Pair ETH/BTC already in pairlist."

    ret = rpc._rpc_blacklist(["*/BTC"])
    assert "StaticPairList" in ret["method"]
    assert len(ret["blacklist"]) == 3
    assert ret["blacklist"] == default_conf["exchange"]["pair_blacklist"]
    assert ret["blacklist"] == ["DOGE/BTC", "HOT/BTC", "ETH/BTC"]
    assert ret["blacklist_expanded"] == ["ETH/BTC"]
    assert "errors" in ret
    assert isinstance(ret["errors"], dict)
    assert ret["errors"] == {"*/BTC": {"error_msg": "Pair */BTC is not a valid wildcard."}}

    ret = rpc._rpc_blacklist(["XRP/.*"])
    assert "StaticPairList" in ret["method"]
    assert len(ret["blacklist"]) == 4
    assert ret["blacklist"] == default_conf["exchange"]["pair_blacklist"]
    assert ret["blacklist"] == ["DOGE/BTC", "HOT/BTC", "ETH/BTC", "XRP/.*"]
    assert ret["blacklist_expanded"] == ["ETH/BTC", "XRP/BTC", "XRP/USDT"]
    assert "errors" in ret
    assert isinstance(ret["errors"], dict)

    ret = rpc._rpc_blacklist_delete(["DOGE/BTC", "HOT/BTC"])

    assert "StaticPairList" in ret["method"]
    assert len(ret["blacklist"]) == 2
    assert ret["blacklist"] == default_conf["exchange"]["pair_blacklist"]
    assert ret["blacklist"] == ["ETH/BTC", "XRP/.*"]
    assert ret["blacklist_expanded"] == ["ETH/BTC", "XRP/BTC", "XRP/USDT"]
    assert "errors" in ret
    assert isinstance(ret["errors"], dict)


def test_rpc_edge_disabled(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    with pytest.raises(RPCException, match=r"Edge is not enabled."):
        rpc._rpc_edge()


def test_rpc_edge_enabled(mocker, edge_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch(
        "coingro.edge.Edge._cached_pairs",
        mocker.PropertyMock(
            return_value={
                "E/F": PairInfo(-0.02, 0.66, 3.71, 0.50, 1.71, 10, 60),
            }
        ),
    )
    coingrobot = get_patched_coingrobot(mocker, edge_conf)

    rpc = RPC(coingrobot)
    ret = rpc._rpc_edge()

    assert len(ret) == 1
    assert ret[0]["Pair"] == "E/F"
    assert ret[0]["Winrate"] == 0.66
    assert ret[0]["Expectancy"] == 1.71
    assert ret[0]["Stoploss"] == -0.02


def test_rpc_health(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    result = rpc._health()
    assert result["last_process"] == "1970-01-01 00:00:00+00:00"
    assert result["last_process_ts"] == 0


def test_rpc_state(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    result = rpc._state()
    assert result["state"] == "running"
    assert result["message"] == ""


def test_rpc_exchange_info(mocker, default_conf) -> None:
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    with pytest.raises(RPCException, match="bad_exchange is not a supported exchange."):
        rpc._rpc_exchange_info("bad_exchange")

    result = rpc._rpc_exchange_info("binance")
    assert result["name"] == "binance"
    assert "required_credentials" in result
    assert isinstance(result["required_credentials"], dict)


def test_rpc_update_exchange(mocker, default_conf) -> None:
    default_conf["runmode"] = RunMode.DRY_RUN
    mock_conf = MagicMock(return_value=default_conf)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch("coingro.rpc.rpc.Configuration.from_files", mock_conf)
    mock_exch = mocker.patch("coingro.rpc.rpc.ExchangeResolver", MagicMock())
    mock_exch.close = MagicMock()
    save_mock = mocker.patch("coingro.rpc.rpc.save_to_config_file", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    with pytest.raises(RPCException, match="bad_exchange is not a supported exchange."):
        rpc._rpc_update_exchange(name="bad_exchange")

    data = {"name": "Kraken", "dry_run": False, "key": "abc", "secret": "123"}
    result = rpc._rpc_update_exchange(**data)
    assert result == {
        "status": "Successfully updated config. " "Reload config for changes to take effect."
    }
    assert save_mock.call_args.args[0]["exchange"]["name"] == "Kraken"
    assert not save_mock.call_args.args[0]["dry_run"]


def test_rpc_update_strategy(mocker, default_conf) -> None:
    default_conf["runmode"] = RunMode.DRY_RUN
    mock_conf = MagicMock(return_value=default_conf)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch("coingro.rpc.rpc.Configuration.from_files", mock_conf)
    save_mock = mocker.patch("coingro.rpc.rpc.save_to_config_file", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)
    with pytest.raises(RPCException, match=r"Impossible to load Strategy 'RandomStrategy'.*"):
        rpc._rpc_update_strategy(strategy="RandomStrategy")

    minimal_roi = [
        {"time_limit_mins": 120, "profit": -1},
        {"time_limit_mins": 60, "profit": 0},
        {"time_limit_mins": 40, "profit": 0.02},
        {"time_limit_mins": 20, "profit": 0.04},
        {"time_limit_mins": 0, "profit": 0.1},
    ]

    data = {
        "strategy": CURRENT_TEST_STRATEGY,
        "minimal_roi": minimal_roi,
        "stoploss": -0.4,
        "trailing_stop": True,
        "trailing_stop_positive": 0.2,
        "trailing_stop_positive_offset": 0.3,
        "trailing_only_offset_is_reached": True,
    }

    result = rpc._rpc_update_strategy(**data)
    assert result == {
        "status": "Successfully updated config. " "Reload config for changes to take effect."
    }
    assert save_mock.call_args.args[0]["strategy"] == CURRENT_TEST_STRATEGY
    assert save_mock.call_args.args[0]["minimal_roi"] == {
        "120": -1,
        "60": 0,
        "40": 0.02,
        "20": 0.04,
        "0": 0.1,
    }
    assert save_mock.call_args.args[0]["stoploss"] == -0.4
    assert save_mock.call_args.args[0]["trailing_stop"]
    assert save_mock.call_args.args[0]["trailing_stop_positive"] == 0.2
    assert save_mock.call_args.args[0]["trailing_stop_positive_offset"] == 0.3
    assert save_mock.call_args.args[0]["trailing_only_offset_is_reached"]


def test_rpc_update_general_settings(mocker, default_conf) -> None:
    default_conf["runmode"] = RunMode.DRY_RUN
    mock_conf = MagicMock(return_value=default_conf)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch("coingro.rpc.rpc.Configuration.from_files", mock_conf)
    save_mock = mocker.patch("coingro.rpc.rpc.save_to_config_file", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)

    data = {
        "max_open_trades": -1,
        "stake_currency": "USDT",
        "stake_amount": 200,
        "tradable_balance_ratio": 0.8,
        "fiat_display_currency": "CAD",
    }

    result = rpc._rpc_update_general_settings(**data)
    assert result == {
        "status": "Successfully updated config. " "Reload config for changes to take effect."
    }
    assert save_mock.call_args.args[0]["max_open_trades"] == -1
    assert save_mock.call_args.args[0]["stake_currency"] == "USDT"
    assert save_mock.call_args.args[0]["stake_amount"] == 200
    assert save_mock.call_args.args[0]["fiat_display_currency"] == "CAD"
    assert save_mock.call_args.args[0]["exchange"]["pair_whitelist"] == [".*/USDT"]

    data = {
        "max_open_trades": 3,
        "stake_amount": "unlimited",
        "tradable_balance_ratio": 0.99,
        "available_capital": 1000,
    }

    result = rpc._rpc_update_general_settings(**data)
    assert result == {
        "status": "Successfully updated config. " "Reload config for changes to take effect."
    }
    assert save_mock.call_args.args[0]["max_open_trades"] == 3
    assert save_mock.call_args.args[0]["stake_amount"] == "unlimited"
    assert save_mock.call_args.args[0]["tradable_balance_ratio"] == 0.99
    assert save_mock.call_args.args[0]["available_capital"] == 1000


def test_rpc_update_all_settings(mocker, default_conf) -> None:
    default_conf["runmode"] = RunMode.DRY_RUN
    mock_conf = MagicMock(return_value=default_conf)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    mocker.patch("coingro.rpc.rpc.Configuration.from_files", mock_conf)
    mock_exch = mocker.patch("coingro.rpc.rpc.ExchangeResolver", MagicMock())
    mock_exch.close = MagicMock()
    save_mock = mocker.patch("coingro.rpc.rpc.save_to_config_file", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)

    minimal_roi = [
        {"time_limit_mins": 120, "profit": -1},
        {"time_limit_mins": 60, "profit": 0},
        {"time_limit_mins": 40, "profit": 0.02},
        {"time_limit_mins": 20, "profit": 0.04},
        {"time_limit_mins": 0, "profit": 0.1},
    ]

    data = {
        "max_open_trades": -1,
        "stake_currency": "USDT",
        "stake_amount": 200,
        "tradable_balance_ratio": 0.8,
        "fiat_display_currency": "CAD",
        "name": "Kraken",
        "dry_run": False,
        "key": "abc",
        "secret": "123",
        "strategy": CURRENT_TEST_STRATEGY,
        "minimal_roi": minimal_roi,
        "stoploss": -0.4,
        "trailing_stop": True,
        "trailing_stop_positive": 0.2,
        "trailing_stop_positive_offset": 0.3,
        "trailing_only_offset_is_reached": True,
    }

    result = rpc._rpc_update_settings(**data)
    assert result == {"status": "Successfully updated config. "}
    assert save_mock.call_args.args[0]["max_open_trades"] == -1
    assert save_mock.call_args.args[0]["stake_currency"] == "USDT"
    assert save_mock.call_args.args[0]["stake_amount"] == 200
    assert save_mock.call_args.args[0]["fiat_display_currency"] == "CAD"
    assert save_mock.call_args.args[0]["exchange"]["pair_whitelist"] == [".*/USDT"]
    assert save_mock.call_args.args[0]["exchange"]["name"] == "Kraken"
    assert not save_mock.call_args.args[0]["dry_run"]
    assert save_mock.call_args.args[0]["strategy"] == CURRENT_TEST_STRATEGY
    assert save_mock.call_args.args[0]["minimal_roi"] == {
        "120": -1,
        "60": 0,
        "40": 0.02,
        "20": 0.04,
        "0": 0.1,
    }
    assert save_mock.call_args.args[0]["stoploss"] == -0.4
    assert save_mock.call_args.args[0]["trailing_stop"]
    assert save_mock.call_args.args[0]["trailing_stop_positive"] == 0.2
    assert save_mock.call_args.args[0]["trailing_stop_positive_offset"] == 0.3
    assert save_mock.call_args.args[0]["trailing_only_offset_is_reached"]


def test_rpc_reset_original_config(mocker, default_conf) -> None:
    config = deepcopy(default_conf)
    config["original_config"] = deepcopy(default_conf)
    mocker.patch("coingro.rpc.telegram.Telegram", MagicMock())
    save_mock = mocker.patch("coingro.rpc.rpc.save_to_config_file", MagicMock())

    coingrobot = get_patched_coingrobot(mocker, config)
    rpc = RPC(coingrobot)

    result = rpc._rpc_reset_original_config()
    assert result == {"status": "Reloading original config ..."}
    assert save_mock.call_args.args[0] == default_conf
    assert coingrobot.state == State.RELOAD_CONFIG

    mock_conf = MagicMock(return_value=default_conf)
    mocker.patch("coingro.rpc.rpc.Configuration.from_files", mock_conf)

    coingrobot = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingrobot)

    result = rpc._rpc_reset_original_config()
    assert result == {"status": "Reloading original config ..."}
    assert save_mock.call_args.args[0] == default_conf
    assert coingrobot.state == State.RELOAD_CONFIG
