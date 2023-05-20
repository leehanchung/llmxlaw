import os
import pprint
import google.generativeai as palm
from dotenv import load_dotenv

load_dotenv()

palm.configure(api_key=os.getenv("PALM_API_KEY"))


models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name
print(f"Using model: {model}")


prompt = """
You are an expert at solving word problems.

Solve the following problem:

I have three houses, each with three cats.
each cat owns 4 mittens, and a hat. Each mitten was
knit from 7m of yarn, each hat from 4m.
How much yarn was needed to make all the items?

Think about it step by step, and show your work.
"""
print(f"Prompt:\n{prompt}")
completion = palm.generate_text(
    model=model,
    prompt=prompt,
    temperature=0,
    # The maximum length of the response
    max_output_tokens=800,
)

print(f"Result:\n{completion.result}")


for model in palm.list_models():
  if 'embedText' in model.supported_generation_methods:
    print(model.name)

x = 'What do squirrels eat?'

close_to_x = 'nuts and acorns'

different_from_x = 'This morning I woke up in San Francisco, and took a walk to the Bay Bridge. It was a good, sunny morning with no fog.'

model = "models/embedding-gecko-001"

# Create an embedding
embedding_x = palm.generate_embeddings(model=model, text=x)
embedding_close_to_x = palm.generate_embeddings(model=model, text=close_to_x)
embedding_different_from_x = palm.generate_embeddings(model=model, text=different_from_x)
