import logging
import os
from langchain.embeddings import OpenAIEmbeddings


def create_vector(text):
    try:
        embeddings = OpenAIEmbeddings()

        doc_result = embeddings.embed_documents([text])

        return doc_result[0]
    except Exception as e:
        logging.error(f"An error has occurred while creating the vector: {e}")
        return None
