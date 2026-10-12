from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

load_dotenv()

QUESTION = "Is the Earth round?"

with TypeSafeClient() as client:  # reads TYPESAFE_API_KEY from the environment
    response = client.system_one(
        state="",  # required by the SDK; nothing to evaluate, just the question
        questions={"answer": Choice(instructions=QUESTION, criteria={"yes": None, "no": None})},
    )

probabilities = response.choices["answer"].probabilities

print(f"Question: {QUESTION}")
print(f"Yes: {probabilities['yes']:.1%}")
print(f"No:  {probabilities['no']:.1%}")
