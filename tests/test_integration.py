from unittest.mock import MagicMock

import pytest

from coingro.enums import ExitCheckTuple, ExitType
from coingro.persistence import Trade
from coingro.persistence.models import Order
from coingro.rpc.rpc import RPC
from tests.conftest import get_patched_coingrobot, patch_get_signal


def test_may_execute_exit_stoploss_on_exchange_multi(default_conf, ticker, fee,
                                                     limit_buy_order, mocker) -> None:
    """
    Tests workflow of selling stoploss_on_exchange.
    Sells
    * first trade as stoploss
    * 2nd trade is kept
    * 3rd trade is sold via sell-signal
    """
    default_conf['max_open_trades'] = 3
    default_conf['exchange']['name'] = 'binance'

    stoploss = {
        'id': 123,
        'info': {}
    }
    stoploss_order_open = {
        "id": "123",
        "timestamp": 1542707426845,
        "datetime": "2018-11-20T09:50:26.845Z",
        "lastTradeTimestamp": None,
        "symbol": "BTC/USDT",
        "type": "stop_loss_limit",
        "side": "sell",
        "price": 1.08801,
        "amount": 90.99181074,
        "cost": 0.0,
        "average": 0.0,
        "filled": 0.0,
        "remaining": 0.0,
        "status": "open",
        "fee": None,
        "trades": None
    }
    stoploss_order_closed = stoploss_order_open.copy()
    stoploss_order_closed['status'] = 'closed'
    stoploss_order_closed['filled'] = stoploss_order_closed['amount']

    # Sell first trade based on stoploss, keep 2nd and 3rd trade open
    stoploss_order_mock = MagicMock(
        side_effect=[stoploss_order_closed, stoploss_order_open, stoploss_order_open])
    # Sell 3rd trade (not called for the first trade)
    should_sell_mock = MagicMock(side_effect=[
        [],
        [ExitCheckTuple(exit_type=ExitType.EXIT_SIGNAL)]]
    )
    cancel_order_mock = MagicMock()
    mocker.patch('coingro.exchange.Binance.stoploss', stoploss)
    mocker.patch.multiple(
        'coingro.exchange.Exchange',
        fetch_ticker=ticker,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
        fetch_stoploss_order=stoploss_order_mock,
        cancel_stoploss_order_with_result=cancel_order_mock,
    )

    mocker.patch.multiple(
        'coingro.coingrobot.CoingroBot',
        create_stoploss_order=MagicMock(return_value=True),
        _notify_exit=MagicMock(),
    )
    mocker.patch("coingro.strategy.interface.IStrategy.should_exit", should_sell_mock)
    wallets_mock = mocker.patch("coingro.wallets.Wallets.update", MagicMock())
    mocker.patch("coingro.wallets.Wallets.get_free", MagicMock(return_value=1000))

    coingro = get_patched_coingrobot(mocker, default_conf)
    coingro.strategy.order_types['stoploss_on_exchange'] = True
    # Switch ordertype to market to close trade immediately
    coingro.strategy.order_types['exit'] = 'market'
    coingro.strategy.confirm_trade_entry = MagicMock(return_value=True)
    coingro.strategy.confirm_trade_exit = MagicMock(return_value=True)
    patch_get_signal(coingro)

    # Create some test data
    coingro.enter_positions()
    assert coingro.strategy.confirm_trade_entry.call_count == 3
    coingro.strategy.confirm_trade_entry.reset_mock()
    assert coingro.strategy.confirm_trade_exit.call_count == 0
    wallets_mock.reset_mock()

    trades = Trade.query.all()
    # Make sure stoploss-order is open and trade is bought (since we mock update_trade_state)
    for trade in trades:
        stoploss_order_closed['id'] = '3'
        oobj = Order.parse_from_ccxt_object(stoploss_order_closed, trade.pair, 'stoploss')

        trade.orders.append(oobj)
        trade.stoploss_order_id = '3'
        trade.open_order_id = None

    n = coingro.exit_positions(trades)
    assert n == 2
    assert should_sell_mock.call_count == 2
    assert coingro.strategy.confirm_trade_entry.call_count == 0
    assert coingro.strategy.confirm_trade_exit.call_count == 1
    coingro.strategy.confirm_trade_exit.reset_mock()

    # Only order for 3rd trade needs to be cancelled
    assert cancel_order_mock.call_count == 1
    # Wallets must be updated between stoploss cancellation and selling, and will be updated again
    # during update_trade_state
    assert wallets_mock.call_count == 4

    trade = trades[0]
    assert trade.exit_reason == ExitType.STOPLOSS_ON_EXCHANGE.value
    assert not trade.is_open

    trade = trades[1]
    assert not trade.exit_reason
    assert trade.is_open

    trade = trades[2]
    assert trade.exit_reason == ExitType.EXIT_SIGNAL.value
    assert not trade.is_open


@pytest.mark.parametrize("balance_ratio,result1", [
                        (1, 200),
                        (0.99, 198),
])
def test_forcebuy_last_unlimited(default_conf, ticker, fee, mocker, balance_ratio, result1) -> None:
    """
    Tests workflow unlimited stake-amount
    Buy 4 trades, forcebuy a 5th trade
    Sell one trade, calculated stake amount should now be lower than before since
    one trade was sold at a loss.
    """
    default_conf['max_open_trades'] = 5
    default_conf['force_entry_enable'] = True
    default_conf['stake_amount'] = 'unlimited'
    default_conf['tradable_balance_ratio'] = balance_ratio
    default_conf['dry_run_wallet'] = 1000
    default_conf['exchange']['name'] = 'binance'
    default_conf['telegram']['enabled'] = True
    mocker.patch('coingro.rpc.telegram.Telegram', MagicMock())
    mocker.patch.multiple(
        'coingro.exchange.Exchange',
        fetch_ticker=ticker,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
    )

    mocker.patch.multiple(
        'coingro.coingrobot.CoingroBot',
        create_stoploss_order=MagicMock(return_value=True),
        _notify_exit=MagicMock(),
    )
    should_sell_mock = MagicMock(side_effect=[
        [],
        [ExitCheckTuple(exit_type=ExitType.EXIT_SIGNAL)],
        [],
        [],
        []]
    )
    mocker.patch("coingro.strategy.interface.IStrategy.should_exit", should_sell_mock)

    coingro = get_patched_coingrobot(mocker, default_conf)
    rpc = RPC(coingro)
    coingro.strategy.order_types['stoploss_on_exchange'] = True
    # Switch ordertype to market to close trade immediately
    coingro.strategy.order_types['exit'] = 'market'
    patch_get_signal(coingro)

    # Create 4 trades
    n = coingro.enter_positions()
    assert n == 4

    trades = Trade.query.all()
    assert len(trades) == 4
    assert coingro.wallets.get_trade_stake_amount('XRP/BTC') == result1

    rpc._rpc_force_entry('TKN/BTC', None)

    trades = Trade.query.all()
    assert len(trades) == 5

    for trade in trades:
        assert trade.stake_amount == result1
        # Reset trade open order id's
        trade.open_order_id = None
    trades = Trade.get_open_trades()
    assert len(trades) == 5
    bals = coingro.wallets.get_all_balances()

    n = coingro.exit_positions(trades)
    assert n == 1
    trades = Trade.get_open_trades()
    # One trade sold
    assert len(trades) == 4
    # stake-amount should now be reduced, since one trade was sold at a loss.
    assert coingro.wallets.get_trade_stake_amount('XRP/BTC') < result1
    # Validate that balance of sold trade is not in dry-run balances anymore.
    bals2 = coingro.wallets.get_all_balances()
    assert bals != bals2
    assert len(bals) == 6
    assert len(bals2) == 5
    assert 'LTC' in bals
    assert 'LTC' not in bals2


def test_dca_buying(default_conf_usdt, ticker_usdt, fee, mocker) -> None:
    default_conf_usdt['position_adjustment_enable'] = True

    coingro = get_patched_coingrobot(mocker, default_conf_usdt)
    mocker.patch.multiple(
        'coingro.exchange.Exchange',
        fetch_ticker=ticker_usdt,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
    )

    patch_get_signal(coingro)
    coingro.enter_positions()

    assert len(Trade.get_trades().all()) == 1
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert pytest.approx(trade.stake_amount) == 60
    assert trade.open_rate == 2.0
    # No adjustment
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert pytest.approx(trade.stake_amount) == 60

    # Reduce bid amount
    ticker_usdt_modif = ticker_usdt.return_value
    ticker_usdt_modif['bid'] = ticker_usdt_modif['bid'] * 0.995
    mocker.patch('coingro.exchange.Exchange.fetch_ticker', return_value=ticker_usdt_modif)

    # additional buy order
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    for o in trade.orders:
        assert o.status == "closed"
    assert trade.stake_amount == 120

    # Open-rate averaged between 2.0 and 2.0 * 0.995
    assert trade.open_rate < 2.0
    assert trade.open_rate > 2.0 * 0.995

    # No action - profit raised above 1% (the bar set in the strategy).
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    assert trade.stake_amount == 120
    assert trade.orders[0].amount == 30
    assert trade.orders[1].amount == 60 / ticker_usdt_modif['bid']

    assert trade.amount == trade.orders[0].amount + trade.orders[1].amount
    assert trade.nr_of_successful_buys == 2
    assert trade.nr_of_successful_entries == 2

    # Sell
    patch_get_signal(coingro, enter_long=False, exit_long=True)
    coingro.process()
    trade = Trade.get_trades().first()
    assert trade.is_open is False
    assert trade.orders[0].amount == 30
    assert trade.orders[0].side == 'buy'
    assert trade.orders[1].amount == 60 / ticker_usdt_modif['bid']
    # Sold everything
    assert trade.orders[-1].side == 'sell'
    assert trade.orders[2].amount == trade.amount

    assert trade.nr_of_successful_buys == 2
    assert trade.nr_of_successful_entries == 2


def test_dca_short(default_conf_usdt, ticker_usdt, fee, mocker) -> None:
    default_conf_usdt['position_adjustment_enable'] = True

    coingro = get_patched_coingrobot(mocker, default_conf_usdt)
    mocker.patch.multiple(
        'coingro.exchange.Exchange',
        fetch_ticker=ticker_usdt,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
    )

    patch_get_signal(coingro, enter_long=False, enter_short=True)
    coingro.enter_positions()

    assert len(Trade.get_trades().all()) == 1
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert pytest.approx(trade.stake_amount) == 60
    assert trade.open_rate == 2.02
    # No adjustment
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert pytest.approx(trade.stake_amount) == 60

    # Reduce bid amount
    ticker_usdt_modif = ticker_usdt.return_value
    ticker_usdt_modif['ask'] = ticker_usdt_modif['ask'] * 1.004
    mocker.patch('coingro.exchange.Exchange.fetch_ticker', return_value=ticker_usdt_modif)

    # additional buy order
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    for o in trade.orders:
        assert o.status == "closed"
    assert pytest.approx(trade.stake_amount) == 120

    # Open-rate averaged between 2.0 and 2.0 * 1.015
    assert trade.open_rate >= 2.02
    assert trade.open_rate < 2.02 * 1.015

    # No action - profit raised above 1% (the bar set in the strategy).
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    assert pytest.approx(trade.stake_amount) == 120
    # assert trade.orders[0].amount == 30
    assert trade.orders[1].amount == 60 / ticker_usdt_modif['ask']

    assert trade.amount == trade.orders[0].amount + trade.orders[1].amount
    assert trade.nr_of_successful_entries == 2

    # Buy
    patch_get_signal(coingro, enter_long=False, exit_short=True)
    coingro.process()
    trade = Trade.get_trades().first()
    assert trade.is_open is False
    # assert trade.orders[0].amount == 30
    assert trade.orders[0].side == 'sell'
    assert trade.orders[1].amount == 60 / ticker_usdt_modif['ask']
    # Sold everything
    assert trade.orders[-1].side == 'buy'
    assert trade.orders[2].amount == trade.amount

    assert trade.nr_of_successful_entries == 2
    assert trade.nr_of_successful_exits == 1


def test_dca_order_adjust(default_conf_usdt, ticker_usdt, fee, mocker) -> None:
    default_conf_usdt['position_adjustment_enable'] = True

    coingro = get_patched_coingrobot(mocker, default_conf_usdt)
    mocker.patch.multiple(
        'coingro.exchange.Exchange',
        fetch_ticker=ticker_usdt,
        get_fee=fee,
        amount_to_precision=lambda s, x, y: y,
        price_to_precision=lambda s, x, y: y,
    )
    mocker.patch('coingro.exchange.Exchange._is_dry_limit_order_filled', return_value=False)

    patch_get_signal(coingro)
    coingro.strategy.custom_entry_price = lambda **kwargs: ticker_usdt['ask'] * 0.96

    coingro.enter_positions()

    assert len(Trade.get_trades().all()) == 1
    trade: Trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert trade.open_order_id is not None
    assert pytest.approx(trade.stake_amount) == 60
    assert trade.open_rate == 1.96
    assert trade.stop_loss_pct is None
    assert trade.stop_loss == 0.0
    assert trade.initial_stop_loss == 0.0
    assert trade.initial_stop_loss_pct is None
    # No adjustment
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 1
    assert trade.open_order_id is not None
    assert pytest.approx(trade.stake_amount) == 60

    # Cancel order and place new one
    coingro.strategy.adjust_entry_price = MagicMock(return_value=1.99)
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    assert trade.open_order_id is not None
    # Open rate is not adjusted yet
    assert trade.open_rate == 1.96
    assert trade.stop_loss_pct is None
    assert trade.stop_loss == 0.0
    assert trade.initial_stop_loss == 0.0
    assert trade.initial_stop_loss_pct is None

    # Fill order
    mocker.patch('coingro.exchange.Exchange._is_dry_limit_order_filled', return_value=True)
    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 2
    assert trade.open_order_id is None
    # Open rate is not adjusted yet
    assert trade.open_rate == 1.99
    assert trade.stop_loss_pct == -0.1
    assert trade.stop_loss == 1.99 * 0.9
    assert trade.initial_stop_loss == 1.99 * 0.9
    assert trade.initial_stop_loss_pct == -0.1

    # 2nd order - not filling
    coingro.strategy.adjust_trade_position = MagicMock(return_value=120)
    mocker.patch('coingro.exchange.Exchange._is_dry_limit_order_filled', return_value=False)

    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 3
    assert trade.open_order_id is not None
    assert trade.open_rate == 1.99
    assert trade.orders[-1].price == 1.96
    assert trade.orders[-1].cost == 120

    # Replace new order with diff. order at a lower price
    coingro.strategy.adjust_entry_price = MagicMock(return_value=1.95)

    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 4
    assert trade.open_order_id is not None
    assert trade.open_rate == 1.99
    assert trade.orders[-1].price == 1.95
    assert pytest.approx(trade.orders[-1].cost) == 120

    # Fill DCA order
    coingro.strategy.adjust_trade_position = MagicMock(return_value=None)
    mocker.patch('coingro.exchange.Exchange._is_dry_limit_order_filled', return_value=True)
    coingro.strategy.adjust_entry_price = MagicMock(side_effect=ValueError)

    coingro.process()
    trade = Trade.get_trades().first()
    assert len(trade.orders) == 4
    assert trade.open_order_id is None
    assert pytest.approx(trade.open_rate) == 1.963153456
    assert trade.orders[-1].price == 1.95
    assert pytest.approx(trade.orders[-1].cost) == 120
    assert trade.orders[-1].status == 'closed'

    assert pytest.approx(trade.amount) == 91.689215
    # Check the 2 filled orders equal the above amount
    assert pytest.approx(trade.orders[1].amount) == 30.150753768
    assert pytest.approx(trade.orders[-1].amount) == 61.538461232
