from app.logic import compute_settlements, compute_shares


def test_example_1_even_split():
    shares = compute_shares(2400, [(1, 1), (2, 2), (3, 1)])
    assert [s["amount_cents"] for s in shares] == [600, 1200, 600]


def test_example_2_rounding_goes_to_first_participant():
    shares = compute_shares(1000, [(3, 1), (1, 1), (2, 1)])
    assert [(s["user_id"], s["amount_cents"]) for s in shares] == [(1, 334), (2, 333), (3, 333)]
    assert sum(s["amount_cents"] for s in shares) == 1000


def test_remainder_is_spread_one_cent_per_portion():
    shares = compute_shares(1000, [(1, 2), (2, 1)])
    assert [s["amount_cents"] for s in shares] == [667, 333]


def test_sum_is_always_exact():
    for amount in range(1, 200):
        for parts in ([(1, 1)], [(1, 1), (2, 3)], [(4, 2), (5, 2), (6, 1)]):
            assert sum(s["amount_cents"] for s in compute_shares(amount, parts)) == amount


def test_example_1_settlements():
    transfers = compute_settlements({1: 1800, 2: -1200, 3: -600})
    assert transfers == [
        {"from_user": 2, "to_user": 1, "amount_cents": 1200},
        {"from_user": 3, "to_user": 1, "amount_cents": 600},
    ]


def test_settlements_are_minimal_and_zero_out_balances():
    balances = {1: 500, 2: 300, 3: -400, 4: -400}
    transfers = compute_settlements(balances)
    assert len(transfers) <= len(balances) - 1
    result = dict(balances)
    for t in transfers:
        result[t["from_user"]] += t["amount_cents"]
        result[t["to_user"]] -= t["amount_cents"]
    assert set(result.values()) == {0}


def test_no_settlement_when_balanced():
    assert compute_settlements({1: 0, 2: 0}) == []
