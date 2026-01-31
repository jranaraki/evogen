""" This is the make code to generate evolving benchmark questions
"""

import json
import logging
import os
import re

from dotenv import load_dotenv

import db
import llm
from logger import get_logger

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)

load_dotenv()
PROMPT_CONFIG = {}
EVOGEN_CONFIG = {}

logger = get_logger()


def init():
    """
    Initialize EVOGEN by loading the configuration files
    :return:
    """
    global PROMPT_CONFIG, EVOGEN_CONFIG

    with open(os.getenv('PROMPT_CONFIG_PATH'), 'r') as prompt_config_file:
        PROMPT_CONFIG = json.load(prompt_config_file)

    if PROMPT_CONFIG is not None:
        logger.info('Loaded prompt config file!')

    with open(os.getenv('EVOGEN_CONFIG_PATH'), 'r') as evogen_config_file:
        EVOGEN_CONFIG = json.load(evogen_config_file)

    if EVOGEN_CONFIG is not None:
        logger.info('Loaded evogen config file!')


def question_generator(model, database):
    """
    Generates a question
    :param model: Model object
    :param database: Database object
    :return: A novel question
    """
    question = None
    messages = [
        {'role': 'user', 'content': PROMPT_CONFIG['generator']}
    ]

    for i in range(int(EVOGEN_CONFIG['retry'])):
        question = model.chat(messages=messages)
        distance_score = database.distance_score(question)
        if distance_score > float(EVOGEN_CONFIG['novelty_threshold']):
            break
        else:
            logger.error(
                f"After {EVOGEN_CONFIG['retry']} retries, still cannot generate novel enough questions! Exiting...")
            exit(0)

    return question


def response_generator(model, input_question):
    """
    Generates a response to the input question
    :param model: Model object
    :param input_question: Input question
    :return: Generated response
    """
    messages = [
        {'role': 'user', 'content': input_question}
    ]
    response = model.chat(messages=messages)
    return response


def scorer(model, input_question, output_response):
    """
    Scores a question against an output response (LLM-as-a-judge)
    :param model: Model object
    :param input_question: Input question
    :param output_response: Output response
    :return: Score value
    """
    messages = [
        {'role': 'user', 'content': PROMPT_CONFIG['scorer'].format(question=input_question, answer=output_response)}
    ]
    response = model.chat(messages=messages)

    try:
        score = float(re.sub(r"\s+", "", response))
    except:
        score = 0
    return score


def exponential_moving_average(data):
    """
    Exponential Moving Average calculator
    :param data: Input data
    :return: The last EMA value
    """
    if not data:
        return []

    multiplier = 2 / (int(EVOGEN_CONFIG['span']) + 1)
    ema_values = [data[0]]
    for i in range(1, len(data)):
        current_ema = (data[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(current_ema)

    return ema_values[-1]


def evolver(model, input_question, input_success_score):
    """
    Evolves the input question to make harder or simpler based on the input score
    :param model: Model object
    :param input_question: Input question
    :param input_success_score: Input success score
    :return: Evolved question
    """
    if input_success_score > 0.75:
        query = PROMPT_CONFIG['harder'].format(question=input_question)
    elif input_success_score < 0.25:
        query = PROMPT_CONFIG['simpler'].format(question=input_question)
    else:
        return input_question

    messages = [
        {'role': 'user', 'content': query}
    ]
    response = model.chat(messages=messages)

    return response


def store_scores(input_scores):
    """
    Stores calculated success scores
    :param input_scores: Input success scores
    :return:
    """
    with open(os.path.join(os.getenv('DATABASE_PATH'), 'scores.json'), "w") as file:
        json.dump(input_scores, file)


def load_scores():
    """
    Loads scores from file
    :return: Scores list
    """
    if os.path.exists(os.path.join(os.getenv('DATABASE_PATH'), 'scores.json')):
        with open(os.path.join(os.getenv('DATABASE_PATH'), 'scores.json'), "r") as file:
            scores = json.load(file)
    else:
        scores = []
    return scores

def run():
    """
    Runs the Self-Evolving Benchmark Generator pipeline
    :return:
    """
    init()
    openai_model = llm.LLMClient()
    database = db.Database()
    success_scores = load_scores()

    try:
        logger.info("Press Ctrl+C to stop...")
        while True:
            question = question_generator(openai_model, database)
            response = response_generator(openai_model, question)
            success_score = scorer(openai_model, question, response)
            success_scores.append(success_score)
            current_ema = exponential_moving_average(success_scores)
            question = evolver(openai_model, question, current_ema)
            database.insert_question(question)
            logger.info(f'#Questions: {database.questions_count()}, Score: {current_ema:.4f}')
    except KeyboardInterrupt:
        database.print_questions()
        store_scores(success_scores)


if __name__ == '__main__':
    run()