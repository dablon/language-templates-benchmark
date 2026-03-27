"""
Compute Service - CPU-intensive benchmark operations
"""

import time

from app import __service__


def fibonacci(n: int) -> int:
    """Calculate fibonacci number recursively"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def is_prime(n: int) -> bool:
    """Check if number is prime"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def execute(n: int = 30) -> dict:
    """
    Execute CPU benchmark: fibonacci + prime calculation

    Args:
        n: Input for fibonacci calculation (capped at 35)

    Returns:
        dict with operation results and timing
    """
    # Cap input to prevent excessive computation
    n_capped = min(max(n, 1), 35)

    start = time.time()

    # Calculate fibonacci
    fib_result = fibonacci(n_capped)

    # Find primes
    primes = [i for i in range(2, min(n_capped * 10, 500)) if is_prime(i)]

    elapsed_ms = (time.time() - start) * 1000

    return {
        "operation": "compute",
        "fibonacci_input": n_capped,
        "fibonacci_value": fib_result,
        "primes_found": len(primes),
        "execution_time_ms": round(elapsed_ms, 2),
        "service": __service__
    }