from sympy import factorint, primepi

SPACE = "  "


def format_factors(factors: dict[int, int]) -> str:
    return " * ".join([f"{k}^{v}" if v > 1 else str(k) for k, v in factors.items()])


def full_factorization(number: int, depth=0, prime=None):
    factors = factorint(number)

    if prime is None:
        print(f"{number} = {format_factors(factors)}")
    elif len(factors) == 1 and list(factors.values())[0] == 1:
        print(SPACE * depth + f"π({prime}) = {number}")
    else:
        print(SPACE * depth + f"π({prime}) = {number} = {format_factors(factors)}")

    for prime in factors:
        if prime > 5:
            prime_number = primepi(prime)
            full_factorization(prime_number, depth + 1, prime=prime)


full_factorization(123123123123123123123)
