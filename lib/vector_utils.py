"""
Pure Python & NumPy Vector utilities for VigilDoc.
Computes TF-IDF vector embeddings and cosine similarity without external scipy/sklearn C-DLL dependencies.
"""

import math
import re
import numpy as np

STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can',
    'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had',
    'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i',
    'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no',
    'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over',
    'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their', 'theirs', 'them',
    'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until',
    'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with',
    'you', 'your', 'yours', 'yourself', 'yourselves'
}

class PureTfidfVectorizer:
    def __init__(self):
        self.vocabulary_ = {}
        self.idf_ = []

    def _tokenize(self, text: str) -> list:
        tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    def fit_transform(self, raw_documents: list) -> np.ndarray:
        tokenized_docs = [self._tokenize(doc) for doc in raw_documents]
        
        # Build vocabulary
        vocab_set = set()
        for doc in tokenized_docs:
            vocab_set.update(doc)
        
        vocab_list = sorted(list(vocab_set))
        self.vocabulary_ = {word: idx for idx, word in enumerate(vocab_list)}

        num_docs = len(raw_documents)
        vocab_size = len(vocab_list)
        
        if vocab_size == 0:
            return np.zeros((num_docs, 1))

        # Calculate Document Frequencies (DF)
        df = np.zeros(vocab_size)
        for doc in tokenized_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                if term in self.vocabulary_:
                    df[self.vocabulary_[term]] += 1

        # Smooth IDF: log((1 + N) / (1 + DF)) + 1
        self.idf_ = np.log((1 + num_docs) / (1 + df)) + 1.0

        # Calculate TF-IDF matrix
        matrix = np.zeros((num_docs, vocab_size))
        for doc_idx, doc in enumerate(tokenized_docs):
            if not doc:
                continue
            doc_len = len(doc)
            term_counts = {}
            for term in doc:
                term_counts[term] = term_counts.get(term, 0) + 1
            
            for term, count in term_counts.items():
                if term in self.vocabulary_:
                    term_idx = self.vocabulary_[term]
                    tf = count / doc_len
                    matrix[doc_idx, term_idx] = tf * self.idf_[term_idx]

        # L2 normalize
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def transform(self, raw_documents: list) -> np.ndarray:
        tokenized_docs = [self._tokenize(doc) for doc in raw_documents]
        num_docs = len(raw_documents)
        vocab_size = len(self.vocabulary_)

        if vocab_size == 0:
            return np.zeros((num_docs, 1))

        matrix = np.zeros((num_docs, vocab_size))
        for doc_idx, doc in enumerate(tokenized_docs):
            if not doc:
                continue
            doc_len = len(doc)
            term_counts = {}
            for term in doc:
                term_counts[term] = term_counts.get(term, 0) + 1
            
            for term, count in term_counts.items():
                if term in self.vocabulary_:
                    term_idx = self.vocabulary_[term]
                    tf = count / doc_len
                    matrix[doc_idx, term_idx] = tf * self.idf_[term_idx]

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

def compute_embeddings(documents: list) -> tuple:
    vectorizer = PureTfidfVectorizer()
    matrix = vectorizer.fit_transform(documents)
    return matrix, vectorizer

def compute_similarity_matrix(embeddings_matrix: np.ndarray) -> np.ndarray:
    # Dot product of normalized vectors equals cosine similarity
    return np.dot(embeddings_matrix, embeddings_matrix.T)

def find_top_k_similar(query_vector: np.ndarray, embeddings_matrix: np.ndarray, top_k: int = 5) -> list:
    similarities = np.dot(query_vector, embeddings_matrix.T)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [(idx, float(similarities[idx])) for idx in top_indices]
