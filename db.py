""" This code include the db to store and evaluate similarity of the questions
"""

import os

import chromadb
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()


class Database:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=os.getenv('DATABASE_PATH'))
        self.collection = self.chroma_client.get_or_create_collection(name='questions', metadata={'hnsw:space': 'cosine'})

    def insert_question(self, question):
        """
        Inserts a question into the database
        :param question: Input question
        :return:
        """
        ids = f'id_{str(self.collection.count() + 1)}'
        self.collection.upsert(documents=[question], ids=ids)

    def distance_score(self, question):
        """
        Calculates the distance between the input question and the database
        :param question: Input question
        :return: Distance score
        """
        results = self.collection.query(query_texts=question, n_results=1)
        try:
            score = results['distances'][0][0]
        except IndexError:
            score = 1
        return score

    def questions_count(self):
        """
        Counts the number of questions in the database
        :return: Number of questions
        """
        return self.collection.count()

    def print_questions(self):
        """
        Prints all the questions in the database
        :return:
        """
        table = [(i + 1, q) for i, q in enumerate(self.collection.get()['documents'])]
        print(tabulate(table, headers=["No.", "Question"]))
