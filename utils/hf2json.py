import json
from datasets import load_dataset
dataset = load_dataset("vietgpt/grade_school_math_rationale_vi")["train"]
dataset = dataset.rename_columns({'question': 'instruction', 'rationale': 'output'})

items = []

for i in dataset:
    items.append({
        'instruction': i['instruction'],
        'output': i['output']
    })

with open('../datasets/GRADE/grade_school_math_rationale_vi.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=4)