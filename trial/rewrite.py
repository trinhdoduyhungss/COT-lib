import pandas as pd
from tools.components.LLMs.open_gpt import OpenGPTBot

gpt = OpenGPTBot()

# Read the data jsonl
data = pd.read_json('D:/Projects/COT-lib/datasets/vnd_gold.jsonl', lines=True, encoding='utf-8', orient='records')

prompt = "I give you a complete answer, your mission is to write a correct question about the objective in the context of the answer. The question must in Vietnamese. Answer: {} Question:"

def gen_question(text):
    question, answer = text.split('\t')
    print("Original question: ", question)
    ask_question = prompt.format(answer)
    gpt_reponse = gpt.ask(ask_question)
    if gpt_reponse and "Tôi xin lỗi" not in gpt_reponse and "Please visit" not in gpt_reponse:
        question = gpt_reponse
    return question


if __name__ == '__main__':
    data['ques_ans'] = data["instruction"] + '\t' + data["output"]

    data['instruction'] = data['ques_ans'].apply(gen_question)

    data.drop(columns=['ques_ans'], inplace=True)

    data.to_json('data_rewrite.jsonl', orient='records', lines=True, force_ascii=False)
