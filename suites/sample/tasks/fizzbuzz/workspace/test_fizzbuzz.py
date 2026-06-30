from fizzbuzz import fizzbuzz


def test_plain_numbers():
    assert fizzbuzz(1) == "1"
    assert fizzbuzz(7) == "7"


def test_single_factors():
    assert fizzbuzz(3) == "Fizz"
    assert fizzbuzz(9) == "Fizz"
    assert fizzbuzz(5) == "Buzz"
    assert fizzbuzz(10) == "Buzz"


def test_both_factors():
    assert fizzbuzz(15) == "FizzBuzz"
    assert fizzbuzz(30) == "FizzBuzz"
    assert fizzbuzz(45) == "FizzBuzz"
