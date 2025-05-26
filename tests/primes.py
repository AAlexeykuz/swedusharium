def segmented_sieve(limit):
    """Segmented Sieve (memory-efficient for large limits)"""
    if limit < 2:
        return []

    sqrt_n = int(limit**0.5) + 1
    sieve = bytearray([True]) * (sqrt_n + 1)
    sieve[0:2] = b"\x00\x00"  # 0 and 1 are not primes

    for i in range(2, sqrt_n + 1):
        if sieve[i]:
            sieve[i * i :: i] = b"\x00" * ((sqrt_n - i * i) // i + 1)

    primes = [i for i, is_prime in enumerate(sieve) if is_prime]

    # Segmented sieve for the remaining range
    low = sqrt_n + 1
    while low <= limit:
        high = min(low + sqrt_n, limit)
        segment = bytearray([True]) * (high - low + 1)

        for p in primes:
            start = max(p * p, ((low + p - 1) // p) * p)
            if start > high:
                break
            segment[start - low :: p] = b"\x00" * ((high - start) // p + 1)

        primes.extend(i + low for i, is_prime in enumerate(segment) if is_prime)
        low += sqrt_n + 1

    return primes


# Example: Print primes ≤ 100
for i, p in enumerate(segmented_sieve(10000), start=1):
    print(i, p)
