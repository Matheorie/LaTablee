"""Règles de calcul des parts et des remboursements, en centimes entiers."""


def compute_shares(amount_cents: int, participants: list[tuple[int, int]]) -> list[dict]:
    """Répartit le montant au prorata des parts.

    participants : liste de (user_id, portions). Le quotient entier est le prix de base
    d'une part. Le reste est distribué à raison d'un centime par part, en parcourant
    les participants par identifiant croissant. La somme est toujours exacte.
    """
    ordered = sorted(participants)
    total_portions = sum(portions for _, portions in ordered)
    base, remainder = divmod(amount_cents, total_portions)
    shares = []
    for user_id, portions in ordered:
        extra = min(portions, remainder)
        remainder -= extra
        shares.append(
            {"user_id": user_id, "portions": portions, "amount_cents": base * portions + extra}
        )
    return shares


def compute_settlements(balances: dict[int, int]) -> list[dict]:
    """Algorithme glouton : le plus gros débiteur rembourse le plus gros créditeur
    du minimum de leurs montants, jusqu'à des soldes nuls."""
    creditors = {u: b for u, b in balances.items() if b > 0}
    debtors = {u: -b for u, b in balances.items() if b < 0}
    transfers = []
    while creditors and debtors:
        debtor = max(debtors, key=lambda u: (debtors[u], -u))
        creditor = max(creditors, key=lambda u: (creditors[u], -u))
        amount = min(debtors[debtor], creditors[creditor])
        transfers.append({"from_user": debtor, "to_user": creditor, "amount_cents": amount})
        debtors[debtor] -= amount
        creditors[creditor] -= amount
        if debtors[debtor] == 0:
            del debtors[debtor]
        if creditors[creditor] == 0:
            del creditors[creditor]
    return transfers
