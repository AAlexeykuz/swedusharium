import math
import random


def is_prime(n):
    """Miller-Rabin primality test"""
    if n < 2:
        return False
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in [2, 325, 9375, 28178, 450775, 9780504, 1795265022]:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def pollards_rho(n):
    """Pollard's Rho algorithm for factorization"""
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
    if n % 5 == 0:
        return 5

    while True:
        c = random.randint(1, n - 1)
        f = lambda x: (pow(x, 2, n) + c) % n
        x, y, d = 2, 2, 1
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


def factor(n):
    """Prime factorization using trial division and Pollard's Rho"""
    if n == 1:
        return []
    if is_prime(n):
        return [n]
    d = pollards_rho(n)
    return factor(d) + factor(n // d)


def prime_factors(n):
    """Return prime factors with exponents"""
    if n == 1:
        return {}
    factors = factor(n)
    result = {}
    for p in factors:
        result[p] = result.get(p, 0) + 1
    return dict(sorted(result.items()))


def factorization_string(n):
    """Return factorization as a formatted string"""
    if n == 1:
        return "1"
    factors = prime_factors(n)
    return " × ".join(f"{p}^{e}" if e > 1 else f"{p}" for p, e in factors.items())


# Example usage
if __name__ == "__main__":
    numbers = [2023]
    for num in numbers:
        print(f"{num} = {factorization_string(num)}")
