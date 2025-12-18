import os
import re
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = "Q: What is 2^{362} (mod 100) " \
"A: Since 363 is greater then 10. We will go ahead and factor the modulus first which breaks" \
"down to 100 = 4 * 25. Now lets compute 2^{362} (mod 4). Lets see powers of 2 modulo 4. 2^{1} is equivalent to 2 (mod 4)" \
"2^{2} is equivalent to 0 (mod 4). We can see that once the exponent is greater then 2, the result stays 0." \
"Since 362 is greater then or equal to 2. We can see that 2^{362} is equivalent to 0 (mod 4). " \
"Now lets compute 2^{362} (mod 25). The gcd(2,25) = 1 and φ(25)=20. So by Euler's theorem: 2^20 is equivalent to 1 (mod 25). " \
"Now lets reduce the exponent 362 mod 20 = 2. So 2^362 is equivalent to 2^2 = 4 (mod 25)." \
"Now lets combine this using the Chinese Remainder Theorem. We now have: x is equivalent to 0 (mod 4). And x is equivalent to 4 (mod 25). " \
"Lets check numbers congruent to 4 mod 25: Since 4 is divisible by 4. The solution modulo 100 is: x = 4. The final answer is 4. "


USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

what is 3^{12345} (mod 100)?
"""


# For this simple example, we expect the final numeric answer only
EXPECTED_OUTPUT = "Answer: 43"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        # Prefer a numeric normalization when possible (supports integers/decimals)
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.3, "num_predict": 512},
        )
        output_text = response.message.content
        final_answer = extract_final_answer(output_text)
        if final_answer.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {final_answer}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)


#Successful Prompt