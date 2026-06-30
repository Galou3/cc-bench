def fizzbuzz(n):
    # BUG: divisible-by-3 is checked before divisible-by-15, so multiples of 15
    # return "Fizz" and the "FizzBuzz" branch below is unreachable.
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    if n % 15 == 0:
        return "FizzBuzz"
    return str(n)
