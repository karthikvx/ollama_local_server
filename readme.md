run ollama local on linux
text parser on docker
web ui to intake file and process thru available models in local

'''

docker run --rm --network host ollama-client



docker run --rm -p 5000:5000 --network host -v ~/Pictures/Screenshots:/root/Pictures/Screenshots -v $(pwd)/output-folder:/app/output-folder img2text




docker run --rm -v ~/Pictures/Screenshots:/root/Pictures/Screenshots -v $(pwd)/output-folder:/app/output-folder img2text python pngs_to_md.py

'''


karthikvx@gmail.com


one file  ( my-applications ) has the jobs applied and second file (search-jobs) has current job list. exclude jobs in my-applications from search-jobs, exclude my-applications inactive jobs titles from search-jobs. group the output result by location   


Answer Generation prompt:

You are a financial assistant. Using only the information provided in the context below, answer the question as concisely and factually as possible. Do not provide explanations, reasoning, or analysis—only provide the answer itself.

Context: {context}
Question: {question}

Answer:

==========================

Evaluator prompt:

Are the two following answers (Answer 1 and Answer 2) the same with respect to the question between single quotes '{question}'?

Answer 1: {ground_truth_answer}
Answer 2: {generated_answer}
Please just give one of the answers: 'true' or 'false'. Do not include any explanation.

Example:
Question: 'What is the capital of France?'
Answer 1: Paris is the capital of France.
Answer 2: The capital of France is Paris.
Answer: true

========================