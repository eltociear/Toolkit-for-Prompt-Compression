from .compressors import PromptCompressor
import sys
sys.path.append('..')
from datasets_helper import Dataset
from typing import List

import time
from transformers import GPT2Tokenizer
import copy
import openai
from openai import OpenAI
import warnings


apikeys = ["Your API keys here",
           "Your API keys here"]
missing = 0
# Edit your GPT demos here
reconstruction_demos = [
    {
        "role": "user",
        "content": """Your answer should start with "Answer: ". Recover the compressed context: A robe takes 2 bolts blue fiber half that much white fiber How many bolts in total? #### 3"""
    },
    {
        "role": "assistant",
        "content": "Answer: A robe takes 2 bolts of blue fiber and half that much white fiber.  How many bolts in total does it take?\n#### 3"
    },
    {
        "role": "user",
        "content": """Your answer should start with "Answer: ". Recover the compressed context: Josh decides try flipping a house He buys a house for then puts in in repairs This increased the value the house by 150% How much profit did he #### 70000"""
    },
    {
        "role": "assistant",
        "content": "Answer: Josh decides to try flipping a house.  He buys a house for $80,000 and then puts in $50,000 in repairs.  This increased the value of the house by 150%.  How much profit did he make?\n####70000"
    },
    {
        "role": "user",
        "content": """Your answer should start with "Answer: ". Recover the compressed context: James decides run 3 sprints 3 a week. He runs 60 meters each sprint. How many total meters does he run a week"""
    },
    {
        "role": "assistant",
        "content": "Answer: James decides to run 3 sprints 3 times a week.  He runs 60 meters each sprint.  How many total meters does he run a week?"
    },
    {
        "role": "user",
        "content": """Your answer should start with "Answer: ". Recover the compressed context: Every day, Wendi feeds each of her chickens three cups mixed chicken feed, containing seeds, mealworms and vegetables to help keep them healthy She gives the chickens their feed in three separate meals. In the morning she gives her flock of chickens 15 cups feed. In the afternoon she gives her chickens another 25 cups feed. How many cups of feed does she need to give her chickens in the final meal of the day if the size Wendi's flock is 20 chickens"""
    },
    {
        "role": "assistant",
        "content": "Answer: Every day, Wendi feeds each of her chickens three cups of mixed chicken feed, containing seeds, mealworms and vegetables to help keep them healthy.  She gives the chickens their feed in three separate meals. In the morning, she gives her flock of chickens 15 cups of feed.  In the afternoon, she gives her chickens another 25 cups of feed.  How many cups of feed does she need to give her chickens in the final meal of the day if the size of Wendi's flock is 20 chickens?"
    }
]
maths_demos = [
    {
        "role": "user",
        "content": """Your answer should only contain a number. Answer the question: A new program had 60 downloads in the first month. The number downloads in the second month was three as many the downloads but then reduced 30% How many downloads did the program have total over the three months"""
    },
    {
        "role": "assistant",
        "content": "Answer: 336"
    },
    {
        "role": "user",
        "content": """Your answer should only contain a number. Answer the question: A robe takes 2 bolts of blue fiber and half that much white fiber.  How many bolts in total does it take?"""
    },
    {
        "role": "assistant",
        "content": "Answer: 3"
    },
    {
        "role": "user",
        "content": """Your answer should only contain a number. Answer the question: James decides to run 3 sprints 3 times a week.  He runs 60 meters each sprint.  How many total meters does he run a week?"""
    },
    {
        "role": "assistant",
        "content": "Answer: 540"
    }
]

def chat_gpt(messages):
    flag = False
    max_retry = 10
    retry = 0
    out = "Nothing to say."
    api_key = apikeys[0]
    model = 'gpt-3.5-turbo-16k'
    temperature = 0
    base_url = "https://api.xi-ai.cn/v1"
    client = OpenAI(api_key=api_key, base_url=base_url)
    while not flag:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            out = response.choices[0].message.content
            flag = True
        except openai.InternalServerError as e:
            print(e)
            time.sleep(10)
            retry += 1
            warnings.warn(f"{e} retry:{retry}")
            continue
        except openai.APIStatusError as e:
            if e.message.startswith("Error code: 307"):
                print(e)
                time.sleep(10)
                retry += 1
                warnings.warn(f"{e} retry:{retry}")
                continue
            if e.message.startswith("Error code: 500"):
                print(e)
                time.sleep(10)
                retry += 1
                warnings.warn(f"{e} retry:{retry}")
                continue
            if e.message.startswith("Error code: 504"):
                print(e)
                time.sleep(10)
                retry += 1
                warnings.warn(f"{e} retry:{retry}")
                continue
            else:
                raise e
        except openai.APIConnectionError as e:
            print(e)
            time.sleep(10)
            retry += 1
            continue
        except Exception as e:
            raise e
    client.close()
    return out


def restore_text(compressed_text, eval_type: str = "reconstruction"):
    global missing
    if eval_type == "reconstruction":
        prompt = """Your answer should start with "Answer: ". Recover the compressed context: {}""".format(compressed_text)
        messages = copy.deepcopy(reconstruction_demos)
        messages.append(
            {"role": "user", "content": prompt}
        )
        restored_text = chat_gpt(messages)
        extracted_text = ""
        if "Answer:" in restored_text:
            answer_index = restored_text.index("Answer:")
            extracted_text = restored_text[answer_index + len("Answer:"):].strip()
        else:
            missing += 1

        return extracted_text
    elif eval_type == "summary":
        prompt = """Your answer should start with "Summary: ". Summary the following context: {}""".format(
            compressed_text)
        messages = []
        messages.append(
            {"role": "user", "content": prompt}
        )
        restored_text = chat_gpt(messages)
        extracted_text = ""
        if "Summary:" in restored_text:
            answer_index = restored_text.index("Summary:")
            extracted_text = restored_text[answer_index + len("Summary:"):].strip()
        else:
            missing += 1
        return extracted_text
    elif eval_type == "maths":
        prompt = """Your answer should only contain a number. Answer the question: {}""".format(compressed_text)
        messages = copy.deepcopy(maths_demos)
        messages.append(
            {"role": "user", "content": prompt}
        )
        restored_text = chat_gpt(messages)
        extracted_text = ""
        if "Answer:" in restored_text:
            answer_index = restored_text.index("Answer:")
            extracted_text = restored_text[answer_index + len("Answer:"):].strip()
        else:
            missing += 1
        return extracted_text
    else:
        return None


def run(compressor: PromptCompressor, dataset: Dataset, metrics: List, ratio: float = 0.5, max_index: int = 5, max_length: int = 1024, target_tokens: int = 3000):
    if dataset.dataset_name in ["bbc", "sharegpt"]:
        original = []
        reconstructed = []
        for i in range(max_index):
            original_prompt = ""
            if dataset.dataset_name == "bbc":
                original_prompt = dataset.data[i]["content"]
                original.append(original_prompt)
            elif dataset.dataset_name == "arxiv":
                original_prompt = dataset.data[i]["text"]
                original.append(original_prompt)
            elif dataset.dataset_name == "sharegpt":
                for x in dataset.data[i]["chat"]:
                    original_prompt += x[1]
                original.append(original_prompt)

            compressed_prompt = compressor.compressgo(original_prompt=original_prompt, ratio=ratio, max_length=max_length)

            result = restore_text(compressed_prompt["compressed_prompt"])

            reconstructed.append(result)

        for j in range(len(metrics)):
            score = metrics[j](original, reconstructed)
            for key in score:
                print(key, score[key])

    if dataset.dataset_name == "LongBench":
        total_score = 0
        for i in range(max_index):
            score = 0
            contexts, question, answer = [dataset.data[i][key] for key in ["context", "input", "answers"]]

            # instruction = "Please complete the code given below."
            # question = question + "\n\nNext line of code:\n"

            # instruction = "Read the following passages and answer the question. Your answer should be short and precise."
            # question = question + "\n\nAnswer:\n"

            # instruction = "Read the following passages and summary them."
            # question = question + "\n\nSummary:\n"

            # instruction = "Read the following example questions and classify the question into the given types."
            # question = "Now classify this question. " + question

            instruction = "Read the following paragraphs and match the statement with the paragraph number you have seen."
            question = "Now match the statement with the number of paragraph. Your Answer should be like 'Paragraph X' where X is a number. " + question

            contexts_list = contexts.split("\n")
            contexts_list = ["\n".join(contexts_list[ii: ii + 4]) for ii in range(0, len(contexts_list), 4)]

            compressed_prompt = compressor.compressgo(
                contexts_list,
                instruction=instruction,
                question=question,
                target_token=target_tokens,
                # ratio=0.66,
                iterative_size=200,
                condition_compare=True,
                condition_in_question="after",
                rank_method="llmlingua",
                use_sentence_level_filter=False,
                context_budget="+200",
                dynamic_context_compression_ratio=0.3,  # enable dynamic_context_compression_ratio
            )
            message = [{"role": "user", "content": compressed_prompt["compressed_prompt"]}]
            result = chat_gpt(message)
            if "\n" in result:
                result = result.split("\n", 1)[0]
            # print("result: ", result)
            # print("true answer: ", answer)
            for an in answer:
                score = max(score, metrics[0](result, an))
            total_score += score
        print(total_score/max_index)

    if dataset.dataset_name == "BBH":
        with open(f"dataset/BBH/cot-prompts/{dataset.subdataset_name}.txt", "r") as f:
            context = f.read()
            prompt = context

        total_score = 0

        for i in range(0, max_index):

            question, answer = [dataset.data["examples"][0][i][key] for key in ["input", "target"]]

            # instruction = "Please complete the code given below."
            # question = question + "\n\nNext line of code:\n"

            # instruction = "Read the following passages and answer the question. Your answer should be short and precise."
            # question = question + "\n\nAnswer:\n"

            # instruction = "Read the following passages and summary them."
            # question = question + "\n\nSummary:\n"

            # instruction = "Read the following example questions and classify the question into the given types."
            # question = "Now classify this question. " + question

            instruction = "Read the following examples and answer the question. Your answer should only contais 'True' or 'False'."
            question = "Question: " + question

            compressed_prompt = compressor.compressgo(original_prompt=prompt, ratio=ratio, question=question, max_length=max_length)

            message = [{"role": "user", "content": instruction + compressed_prompt["compressed_prompt"] + question}]

            result = chat_gpt(message)
            # print("result: ", result)
            # print("true answer: ", answer)
            if dataset.subdataset_name == "boolean_expressions":
                if answer == result:
                    total_score += 1
            elif answer in result:
                total_score += 1

        print("Average score: ", total_score / max_index)

    if dataset.dataset_name in ["gigaword", "duc2004", "bnc", "google", "broadcast"]:
        original = []
        reconstructed = []
        for i in range(max_index):
            original_prompt = dataset.data[i]["text"]
            target = dataset.data[i]["summaries"][0]
            original.append(target)

            compressed_prompt = compressor.compressgo(original_prompt=original_prompt, ratio=ratio, max_length=max_length)

            reconstructed.append(compressed_prompt["compressed_prompt"])

        for j in range(len(metrics)):
            score = metrics[j](original, reconstructed)
            for key in score:
                print(key, score[key])

    if dataset.dataset_name in ["arxiv"]:
        reconstructed = []
        reference_lst = []
        for i in range(max_index):
            original_prompt = dataset.data[i]["text"]
            reference = restore_text(original_prompt)

            reference_lst.append(reference)

            compressed_prompt = compressor.compressgo(original_prompt=original_prompt, ratio=ratio, max_length=max_length)

            result = restore_text(compressed_prompt["compressed_prompt"], eval_type="summary")

            reconstructed.append(result)

        for j in range(len(metrics)):
            score = metrics[j](reference_lst, reconstructed)
            for key in score:
                print(key, score[key])

    if dataset.dataset_name in ["GSM"]:
        score = 0
        for i in range(max_index):
            qn = dataset.data[i]["question"]
            an = dataset.data[i]["answer"]
            extracted_text = ""
            if "#### " in an:
                answer_index = an.index("#### ")
                extracted_text = an[answer_index:-len("<|endoftext|>")].strip()
            original_prompt = qn + extracted_text

            compressed_prompt = compressor.compressgo(original_prompt=original_prompt, ratio=ratio,
                                                      max_length=max_length)

            result = restore_text(compressed_prompt["compressed_prompt"], eval_type="maths")

            if extracted_text == result:
                score += 1
        print("Average score: ", score/max_index)
