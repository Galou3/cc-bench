const test = require("node:test");
const assert = require("node:assert");
const { fizzbuzz } = require("./fizzbuzz");

test("plain numbers", () => {
  assert.strictEqual(fizzbuzz(1), "1");
  assert.strictEqual(fizzbuzz(7), "7");
});

test("single factors", () => {
  assert.strictEqual(fizzbuzz(3), "Fizz");
  assert.strictEqual(fizzbuzz(5), "Buzz");
});

test("both factors", () => {
  assert.strictEqual(fizzbuzz(15), "FizzBuzz");
  assert.strictEqual(fizzbuzz(30), "FizzBuzz");
});
