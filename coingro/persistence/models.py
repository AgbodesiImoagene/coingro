"""
This module contains the class to persist trades into SQLite
"""
import logging
import random
import time

from sqlalchemy import create_engine, event, select  # inspect
from sqlalchemy.exc import DBAPIError, NoSuchModuleError, OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy_utils import create_database, database_exists

from coingro.exceptions import OperationalException, TemporaryError
from coingro.misc import retrier
from coingro.persistence.base import _DECL_BASE
from coingro.persistence.migrations import set_sqlite_to_wal  # check_migrate
from coingro.persistence.pairlock import PairLock
from coingro.persistence.pairlock import set_dry_run as set_pairlock_dry_run
from coingro.persistence.trade_model import Order, Trade
from coingro.persistence.trade_model import set_dry_run as set_trade_dry_run

logger = logging.getLogger(__name__)


_SQL_DOCS_URL = "http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls"


def ping_connection(connection, branch):
    """
    Pessimistic SQLAlchemy disconnect handling. Ensures that each
    connection returned from the pool is properly connected to the database.

    http://docs.sqlalchemy.org/en/rel_1_1/core/pooling.html#disconnect-handling-pessimistic
    """
    if branch:
        # "branch" refers to a sub-connection of a connection,
        # we don't want to bother pinging on these.
        return

    start = time.time()
    backoff = 0.2
    reconnect_timeout_seconds = 150
    max_backoff_seconds = 120
    # turn off "close with result".  This flag is only used with
    # "connectionless" execution, otherwise will be False in any case
    save_should_close_with_result = connection.should_close_with_result

    while True:
        connection.should_close_with_result = False

        try:
            connection.scalar(select([1]))
            commit = getattr(connection, "commit", None)
            if callable(commit):
                connection.commit()
            # If we made it here then the connection appears to be healthy
            break
        except DBAPIError as err:
            if time.time() - start >= reconnect_timeout_seconds:
                logger.error(
                    "Failed to re-establish DB connection within %s secs: %s",
                    reconnect_timeout_seconds,
                    err,
                )
                raise OperationalException(err)
            # if err.connection_invalidated:
            logger.warning("DB connection invalidated. Reconnecting...")

            # Use a truncated binary exponential backoff. Also includes
            # a jitter to prevent the thundering herd problem of
            # simultaneous client reconnects
            backoff += backoff * random.random()
            time.sleep(min(backoff, max_backoff_seconds))

            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            continue
            # else:
            #     logger.error(
            #         "Unknown database connection error. Not retrying: %s",
            #         err)
            #     raise OperationalException(err)
        finally:
            # restore "close with result"
            connection.should_close_with_result = save_should_close_with_result


def init_db(db_url: str, dry_run: bool) -> None:
    """
    Initializes this module with the given config,
    registers all known command handlers
    and starts polling for message updates
    :param db_url: Database to use
    :return: None
    """
    kwargs = {}

    if db_url == "sqlite:///":
        raise OperationalException(
            f"Bad db-url {db_url}. For in-memory database, please use `sqlite://`."
        )
    if db_url == "sqlite://":
        kwargs.update(
            {
                "poolclass": StaticPool,
            }
        )
    # Take care of thread ownership
    if db_url.startswith("sqlite://"):
        kwargs.update(
            {
                "connect_args": {"check_same_thread": False},
            }
        )

    try:
        engine = create_engine(db_url, future=True, **kwargs)
    except NoSuchModuleError:
        raise OperationalException(
            f"Given value for db_url: '{db_url}' "
            f"is no valid database URL! (See {_SQL_DOCS_URL})"
        )

    event.listen(engine, "engine_connect", ping_connection)

    set_trade_dry_run(dry_run)
    set_pairlock_dry_run(dry_run)

    create_db(db_url)

    # https://docs.sqlalchemy.org/en/13/orm/contextual.html#thread-local-scope
    # Scoped sessions proxy requests to the appropriate thread-local session.
    # We should use the scoped_session object - not a seperately initialized version
    Trade._session = scoped_session(sessionmaker(bind=engine, autoflush=True))
    Trade.query = Trade._session.query_property()
    Order.query = Trade._session.query_property()
    PairLock.query = Trade._session.query_property()

    # previous_tables = inspect(engine).get_table_names()
    _DECL_BASE.metadata.create_all(engine)
    # check_migrate(engine, decl_base=_DECL_BASE, previous_tables=previous_tables)
    set_sqlite_to_wal(engine)


@retrier
def create_db(db_url: str) -> None:
    # Create database if it does not exist. User must have create database privileges.
    try:
        if not database_exists(db_url):
            create_database(db_url)
    except OperationalError as e:
        raise TemporaryError(
            f"Could not connect to database due to {e.__class__.__name__}. Message: {e}"
        ) from e


def cleanup_db() -> None:
    """
    Flushes all pending operations to disk.
    :return: None
    """
    Trade.commit()
