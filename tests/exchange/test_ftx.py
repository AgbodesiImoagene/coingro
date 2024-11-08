# from random import randint
# from unittest.mock import MagicMock

# import ccxt
# import pytest

# from coingro.exceptions import DependencyException, InvalidOrderException
# from coingro.exchange.common import API_FETCH_ORDER_RETRY_COUNT
# from tests.conftest import get_patched_exchange

# from .test_exchange import ccxt_exceptionhandlers

# STOPLOSS_ORDERTYPE = "stop"


# @pytest.mark.parametrize(
#     "order_price,exchangelimitratio,side",
#     [
#         (217.8, 1.05, "sell"),
#         (222.2, 0.95, "buy"),
#     ],
# )
# def test_stoploss_order_ftx(default_conf, mocker, order_price, exchangelimitratio, side):
#     api_mock = MagicMock()
#     order_id = "test_prod_buy_{}".format(randint(0, 10**6))

#     api_mock.create_order = MagicMock(return_value={"id": order_id, "info": {"foo": "bar"}})

#     default_conf["dry_run"] = False
#     mocker.patch("coingro.exchange.Exchange.amount_to_precision", lambda s, x, y: y)
#     mocker.patch("coingro.exchange.Exchange.price_to_precision", lambda s, x, y: y)

#     exchange = get_patched_exchange(mocker, default_conf, api_mock, "ftx")

#     # stoploss_on_exchange_limit_ratio is irrelevant for ftx market orders
#     order = exchange.stoploss(
#         pair="ETH/BTC",
#         amount=1,
#         stop_price=190,
#         side=side,
#         order_types={"stoploss_on_exchange_limit_ratio": exchangelimitratio},
#         leverage=1.0,
#     )

#     assert api_mock.create_order.call_args_list[0][1]["symbol"] == "ETH/BTC"
#     assert api_mock.create_order.call_args_list[0][1]["type"] == STOPLOSS_ORDERTYPE
#     assert api_mock.create_order.call_args_list[0][1]["side"] == side
#     assert api_mock.create_order.call_args_list[0][1]["amount"] == 1
#     assert "orderPrice" not in api_mock.create_order.call_args_list[0][1]["params"]
#     assert "stopPrice" in api_mock.create_order.call_args_list[0][1]["params"]
#     assert api_mock.create_order.call_args_list[0][1]["params"]["stopPrice"] == 190

#     assert api_mock.create_order.call_count == 1

#     api_mock.create_order.reset_mock()

#     order = exchange.stoploss(
#         pair="ETH/BTC", amount=1, stop_price=220, order_types={}, side=side, leverage=1.0
#     )

#     assert "id" in order
#     assert "info" in order
#     assert order["id"] == order_id
#     assert api_mock.create_order.call_args_list[0][1]["symbol"] == "ETH/BTC"
#     assert api_mock.create_order.call_args_list[0][1]["type"] == STOPLOSS_ORDERTYPE
#     assert api_mock.create_order.call_args_list[0][1]["side"] == side
#     assert api_mock.create_order.call_args_list[0][1]["amount"] == 1
#     assert "orderPrice" not in api_mock.create_order.call_args_list[0][1]["params"]
#     assert api_mock.create_order.call_args_list[0][1]["params"]["stopPrice"] == 220

#     api_mock.create_order.reset_mock()
#     order = exchange.stoploss(
#         pair="ETH/BTC",
#         amount=1,
#         stop_price=220,
#         order_types={"stoploss": "limit"},
#         side=side,
#         leverage=1.0,
#     )

#     assert "id" in order
#     assert "info" in order
#     assert order["id"] == order_id
#     assert api_mock.create_order.call_args_list[0][1]["symbol"] == "ETH/BTC"
#     assert api_mock.create_order.call_args_list[0][1]["type"] == STOPLOSS_ORDERTYPE
#     assert api_mock.create_order.call_args_list[0][1]["side"] == side
#     assert api_mock.create_order.call_args_list[0][1]["amount"] == 1
#     assert "orderPrice" in api_mock.create_order.call_args_list[0][1]["params"]
#     assert api_mock.create_order.call_args_list[0][1]["params"]["orderPrice"] == order_price
#     assert api_mock.create_order.call_args_list[0][1]["params"]["stopPrice"] == 220

#     # test exception handling
#     with pytest.raises(DependencyException):
#         api_mock.create_order = MagicMock(side_effect=ccxt.InsufficientFunds("0 balance"))
#         exchange = get_patched_exchange(mocker, default_conf, api_mock, "ftx")
#         exchange.stoploss(
#             pair="ETH/BTC", amount=1, stop_price=220, order_types={}, side=side, leverage=1.0
#         )

#     with pytest.raises(InvalidOrderException):
#         api_mock.create_order = MagicMock(
#             side_effect=ccxt.InvalidOrder("ftx Order would trigger immediately.")
#         )
#         exchange = get_patched_exchange(mocker, default_conf, api_mock, "ftx")
#         exchange.stoploss(
#             pair="ETH/BTC", amount=1, stop_price=220, order_types={}, side=side, leverage=1.0
#         )

#     ccxt_exceptionhandlers(
#         mocker,
#         default_conf,
#         api_mock,
#         "ftx",
#         "stoploss",
#         "create_order",
#         retries=1,
#         pair="ETH/BTC",
#         amount=1,
#         stop_price=220,
#         order_types={},
#         side=side,
#         leverage=1.0,
#     )


# @pytest.mark.parametrize("side", [("sell"), ("buy")])
# def test_stoploss_order_dry_run_ftx(default_conf, mocker, side):
#     api_mock = MagicMock()
#     default_conf["dry_run"] = True
#     mocker.patch("coingro.exchange.Exchange.amount_to_precision", lambda s, x, y: y)
#     mocker.patch("coingro.exchange.Exchange.price_to_precision", lambda s, x, y: y)

#     exchange = get_patched_exchange(mocker, default_conf, api_mock, "ftx")

#     api_mock.create_order.reset_mock()

#     order = exchange.stoploss(
#         pair="ETH/BTC", amount=1, stop_price=220, order_types={}, side=side, leverage=1.0
#     )

#     assert "id" in order
#     assert "info" in order
#     assert "type" in order

#     assert order["type"] == STOPLOSS_ORDERTYPE
#     assert order["price"] == 220
#     assert order["amount"] == 1


# @pytest.mark.parametrize(
#     "sl1,sl2,sl3,side", [(1501, 1499, 1501, "sell"), (1499, 1501, 1499, "buy")]
# )
# def test_stoploss_adjust_ftx(mocker, default_conf, sl1, sl2, sl3, side):
#     exchange = get_patched_exchange(mocker, default_conf, id="ftx")
#     order = {
#         "type": STOPLOSS_ORDERTYPE,
#         "price": 1500,
#     }
#     assert exchange.stoploss_adjust(sl1, order, side=side)
#     assert not exchange.stoploss_adjust(sl2, order, side=side)
#     # Test with invalid order case ...
#     order["type"] = "stop_loss_limit"
#     assert not exchange.stoploss_adjust(sl3, order, side=side)


# @pytest.mark.usefixtures("init_persistence")
# def test_fetch_stoploss_order_ftx(default_conf, mocker, limit_sell_order, limit_buy_order):
#     default_conf["dry_run"] = True
#     order = MagicMock()
#     order.myid = 123
#     exchange = get_patched_exchange(mocker, default_conf, id="ftx")
#     exchange._dry_run_open_orders["X"] = order
#     assert exchange.fetch_stoploss_order("X", "TKN/BTC").myid == 123

#     with pytest.raises(InvalidOrderException, match=r"Tried to get an invalid dry-run-order.*"):
#         exchange.fetch_stoploss_order("Y", "TKN/BTC")

#     default_conf["dry_run"] = False
#     api_mock = MagicMock()
#     api_mock.fetch_orders = MagicMock(return_value=[{"id": "X", "status": "456"}])
#     exchange = get_patched_exchange(mocker, default_conf, api_mock, id="ftx")
#     assert exchange.fetch_stoploss_order("X", "TKN/BTC")["status"] == "456"

#     api_mock.fetch_orders = MagicMock(return_value=[{"id": "Y", "status": "456"}])
#     exchange = get_patched_exchange(mocker, default_conf, api_mock, id="ftx")
#     with pytest.raises(InvalidOrderException, match=r"Could not get stoploss order for id X"):
#         exchange.fetch_stoploss_order("X", "TKN/BTC")["status"]

#     # stoploss Limit order
#     api_mock.fetch_orders = MagicMock(
#         return_value=[
#             {
#                 "id": "X",
#                 "status": "closed",
#                 "info": {
#                     "orderId": "mocked_limit_sell",
#                 },
#             }
#         ]
#     )
#     api_mock.fetch_order = MagicMock(return_value=limit_sell_order)

#     # No orderId field - no call to fetch_order
#     resp = exchange.fetch_stoploss_order("X", "TKN/BTC")
#     assert resp
#     assert api_mock.fetch_order.call_count == 1
#     assert resp["id_stop"] == "mocked_limit_sell"
#     assert resp["id"] == "X"
#     assert resp["type"] == "stop"
#     assert resp["status_stop"] == "triggered"

#     # Stoploss market order
#     # Contains no new Order, but "average" instead
#     order = {"id": "X", "status": "closed", "info": {"orderId": None}, "average": 0.254}
#     api_mock.fetch_orders = MagicMock(return_value=[order])
#     api_mock.fetch_order.reset_mock()
#     resp = exchange.fetch_stoploss_order("X", "TKN/BTC")
#     assert resp
#     # fetch_order not called (no regular order ID)
#     assert api_mock.fetch_order.call_count == 0
#     assert order == order

#     with pytest.raises(InvalidOrderException):
#         api_mock.fetch_orders = MagicMock(side_effect=ccxt.InvalidOrder("Order not found"))
#         exchange = get_patched_exchange(mocker, default_conf, api_mock, id="ftx")
#         exchange.fetch_stoploss_order(order_id="_", pair="TKN/BTC")
#     assert api_mock.fetch_orders.call_count == 1

#     ccxt_exceptionhandlers(
#         mocker,
#         default_conf,
#         api_mock,
#         "ftx",
#         "fetch_stoploss_order",
#         "fetch_orders",
#         retries=API_FETCH_ORDER_RETRY_COUNT + 1,
#         order_id="_",
#         pair="TKN/BTC",
#     )


# def test_get_order_id(mocker, default_conf):
#     exchange = get_patched_exchange(mocker, default_conf, id="ftx")
#     order = {
#      	  "type": STOPLOSS_ORDERTYPE,
#      	  "price": 1500,
#      	  "id": "1111",
#      	  "id_stop": "1234",
#      	  "info": {}
#     }
#     assert exchange.get_order_id_conditional(order) == "1234"

#     order = {"type": "limit", "price": 1500, "id": "1111", "id_stop": "1234", "info": {}}
#     assert exchange.get_order_id_conditional(order) == "1111"
