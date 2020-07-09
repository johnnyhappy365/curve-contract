import itertools

import brownie
import pytest

from tests.conftest import PRECISIONS

INITIAL_AMOUNTS = [10**(i+6) for i in PRECISIONS]


@pytest.fixture(scope="module", autouse=True)
def setup(alice, bob, aave_coins, underlying_coins, swap):
    for coin, amount in zip(aave_coins, INITIAL_AMOUNTS):
        coin._mint_for_testing(alice, amount, {'from': alice})
        coin.approve(swap, 2**256-1, {'from': alice})

    for coin in underlying_coins:
        coin.approve(swap, 2**256-1, {'from': bob})

    swap.add_liquidity(INITIAL_AMOUNTS, 0, {'from': alice})


@pytest.mark.parametrize("sending,receiving", itertools.permutations([0, 1, 2], 2))
def test_underlying_min_dy_too_high(bob, swap, underlying_coins, sending, receiving):
    amount = 10**PRECISIONS[sending]

    underlying_coins[sending]._mint_for_testing(bob, amount, {'from': bob})

    min_dy = swap.get_dy(sending, receiving, amount)
    with brownie.reverts("Exchange resulted in fewer coins than expected"):
        swap.exchange_underlying(sending, receiving, amount, min_dy+1, {'from': bob})


@pytest.mark.parametrize("sending,receiving", itertools.permutations([0, 1, 2], 2))
def test_underlying_insufficient_balance(bob, swap, underlying_coins, sending, receiving):
    amount = 10**PRECISIONS[sending]

    underlying_coins[sending]._mint_for_testing(bob, amount, {'from': bob})
    with brownie.reverts():
        swap.exchange_underlying(sending, receiving, amount+1, 0, {'from': bob})


@pytest.mark.parametrize("idx", range(3))
def test_same_coin(bob, swap, aave_coins, idx):
    with brownie.reverts("dev: same coin"):
        swap.exchange_underlying(idx, idx, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [-1, -2**127])
def test_i_below_zero(bob, swap, aave_coins, idx):
    with brownie.reverts():
        swap.exchange_underlying(idx, 0, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [3, 2**127-1])
def test_i_above_n_coins(bob, swap, aave_coins, idx):
    with brownie.reverts():
        swap.exchange_underlying(idx, 0, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [-1, -2**127])
def test_j_below_zero(bob, swap, aave_coins, idx):
    with brownie.reverts("dev: j below zero"):
        swap.exchange_underlying(0, idx, 0, 0, {'from': bob})


@pytest.mark.parametrize("idx", [3, 2**127-1])
def test_j_above_n_coins(bob, swap, aave_coins, idx):
    with brownie.reverts("dev: j above N_COINS"):
        swap.exchange_underlying(0, idx, 0, 0, {'from': bob})
