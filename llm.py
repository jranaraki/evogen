""" This code created an LLM client and submits requests to
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from logger import get_logger

load_dotenv()
logger = get_logger()


class LLMClient:
    def __init__(self):
        """
        Initialize the client
        """
        with open(os.getenv('MODEL_CONFIG_PATH'), 'r') as model_config_file:
            self.model_config = json.load(model_config_file)

        if self.model_config['provider'] == 'openai':
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        elif self.model_config['provider'] == 'ollama':
            self.client = OpenAI(base_url=self.model_config['base_url'],
                                 api_key=os.getenv('OPENAI_API_KEY'))
        else:
            logger.error("Invalid provider")

    def chat(self, messages):
        """
        Submit messages to LLM
        :param messages: Input messages
        :return: Generated response
        """
        response = self.client.chat.completions.create(
            model=self.model_config['model'],
            messages=messages,
        )

        return response.choices[0].message.content

