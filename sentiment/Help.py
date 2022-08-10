#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 15:43:18 2022

@author: philiptrettenero
"""

import numpy as np # linear algebra
import pandas as pd # data processing
# Libraries and packages for text (pre-)processing
import string
import re
import nltk
# nltk.download('stopwords')
from gensim.models import Word2Vec
# For type hinting
from typing import List


#https://github.com/towardsNLP/IMDB-Semantic-Sentiment-Analysis/blob/main/Word2Vec/src/w2v_utils.py
class Tokenizer:
    """ After cleaning and denoising steps, in this class the text is broken up into tokens.
    if clean: clean the text from all non-alphanumeric characters,
    if lower: convert the text into lowercase,
    If de_noise: remove HTML and URL components,
    if remove_stop_words: and remove stop-words,
    If keep_neagation: attach the negation tokens to the next token
     and treat them as a single word before removing the stopwords

    Returns:
    List of tokens
    """
    # initialization method to create the default instance constructor for the class
    def __init__(self,
                 clean: bool = True,
                 lower: bool = True,
                 de_noise: bool = True,
                 remove_stop_words: bool = True,
                keep_negation: bool = True) -> List[str]:

        self.de_noise = de_noise
        self.remove_stop_words = remove_stop_words
        self.clean = clean
        self.lower = lower
        self.stopwords = nltk.corpus.stopwords.words('english')
        self.keep_negation = keep_negation

    # other methods
    def denoise(self, text: str) -> str:
        """
        Removing html and URL components
        """
        html_pattern = r"<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"
        url_pattern = r"((http://)[^ ]*|(https://)[^ ]*|(www\.)[^ ]*)"

        text = re.sub(html_pattern, " ", text)
        text = re.sub(url_pattern," ",text).strip()
        return text


    def remove_stopwords(self, tokenized_text: List[str]) -> List[str]:
        text = [word for word in tokenized_text if word not in self.stopwords]
        return text


    def keep_negation_sw(self, text: str) -> str:
        """
        A function to save negation words (n't, not, no) from removing as stopwords
        """
        # to replace "n't" with "not"
        text = re.sub(r"won\'t", "will not", text)
        text = re.sub(r"can\'t", "can not", text)
        text = re.sub(r"n\'t", " not", text)
        # to join not/no into the next word
        text = re.sub("not ", " NOT", text)
        text = re.sub("no ", " NO", text)
        return text


    def tokenize(self, text: str) -> List[str]:
        """
        A function to tokenize words of the text
        """
        non_alphanumeric_pattern =r"[^a-zA-Z0-9]"

        # to substitute multiple whitespace with single whitespace
        text = ' '.join(text.split())

        if self.de_noise:
            text = self.denoise(text)
        if self.lower:
            text = text.lower()
        if self.keep_negation:
            text = self.keep_negation_sw(text)

        if self.clean:
            # to remove non-alphanumeric characters
            text = re.sub(non_alphanumeric_pattern," ", text).strip()

        tokenized_text = text.split()

        if self.remove_stop_words:
            tokenized_text = self.remove_stopwords(tokenized_text)

        return tokenized_text

def w2v_trainer(doc_tokens: List[str],
                epochs: int = 10,
                workers: int = 3,
                vector_size: int = 300,
                window: int = 5,
                min_count: int = 2):
    """
    Going through a list of lists, where each list within the main list contains a set of tokens from a doc, this function trains a Word2Vec model,
    then creates two objects to store keyed vectors and keyed vocabs
    Parameters:
    doc_tokens   : A tokenized document
    epochs       : Number of epochs training over the corpus
    workers      : Number of processors (parallelization)
    vector_size  : Dimensionality of word embeddings
    window       : Context window for words during training
    min_count    : Ignore words that appear less than this
    Returns:
    keyed_vectors       : A word2vec vocabulary model
    keyed_vocab

    """
    w2v_model = Word2Vec(doc_tokens,
                         epochs=10,
                         workers=3,
                         vector_size=300,
                         window=5,
                         min_count=2)

    # create objects to store keyed vectors and keyed vocabs
    keyed_vectors = w2v_model.wv
    keyed_vocab = keyed_vectors.key_to_index

    return keyed_vectors, keyed_vocab



def calculate_overall_similarity_score(keyed_vectors,
                             target_tokens: List[str],
                             doc_tokens: List[str]) -> float:
    """
    Going through a tokenized doc, this function computes vector similarity between
    doc_tokens and target_tokens as 2 lists by n_similarity(list1, list2) method based on
    Word2Vec vocabulary (keyed_vectors),
    then returns the similarity scores.

    Parameters:
    target_tokens  : A set of semantically co-related words
    doc_tokens     : A tokenized document
    keyed_vectors  : A word2vec vocabulary model

    Returns:
    vector similarity scores between 2 tokenized list doc_tokens and target_tokens
    """

    target_tokens = [token for token in target_tokens if token in keyed_vectors]

    doc_tokens = [token for token in doc_tokens if token in keyed_vectors]

    similarity_score = keyed_vectors.n_similarity(target_tokens, doc_tokens)

    return similarity_score


def overall_semantic_sentiment_analysis (keyed_vectors,
                                         positive_target_tokens: List[str],
                                         negative_target_tokens: List[str],
                                         doc_tokens: List[str],
                                         doc_is_series: bool = True) -> float:
    """
    This function calculates the semantic sentiment of the text.
    It first computes a  vector for the text (average of the  wordvectors building the text document vector)
    and two vectors representing our given positive and negative lists of words
    and then calculates Positive and Negative Sentiment Scores as cosine similarity
    between the text vector and the positive and negative vectors respectively.

    Parameters:
    keyed_vectors           : A word2vec vocabulary model
    positive_target_tokens  : A list of sentiment or opinion words that indicate positive opinions
    negative_target_tokens  : A list of sentiment or opinion words that indicate negative opinions
    doc_tokens              : A tokenized document


    Returns:
    positive_score : vector similarity scores between doc_tokens and positive_target_tokens
    negative_score : vector similarity scores between doc_tokens and negative_target_tokens

    semantic_sentiment_score  : positive_score - negative_score
    semantic_sentiment_polarity : Overall score: 0 for more negative or 1 for more positive doc
    """

    positive_score = doc_tokens.apply(lambda x: calculate_overall_similarity_score(keyed_vectors=keyed_vectors,
                                                                 target_tokens=positive_target_tokens,
                                                                 doc_tokens=x))

    negative_score = doc_tokens.apply(lambda x: calculate_overall_similarity_score(keyed_vectors=keyed_vectors,
                                                                 target_tokens=negative_target_tokens,
                                                                 doc_tokens=x))

    semantic_sentiment_score = positive_score - negative_score

    semantic_sentiment_polarity = semantic_sentiment_score.apply(lambda x: 1 if (x > 0) else 0)

    return positive_score, negative_score, semantic_sentiment_score, semantic_sentiment_polarity


def list_similarity(keyed_vectors,
                    wordlist1: List[str],
                    wordlist2: List[str]) -> pd.Series:
    """ A function to calculate vector similarity between 2 lists of tokens"""
    wv1= np.array([keyed_vectors[wd] for wd in wordlist1 if wd in keyed_vectors])
    wv2= np.array([keyed_vectors[wd] for wd in wordlist2 if wd in keyed_vectors])
    wv1 /= np.linalg.norm(wv1, axis=1)[:, np.newaxis]
    try:
        wv2 /= np.linalg.norm(wv2, axis=1)[:, np.newaxis]
    except:
        wv2 = np.zeros(np.shape(wv1))
        print("Error caught and handled.")
    return np.dot(wv1, np.transpose(wv2))

def calculate_topn_similarity_score(keyed_vectors,
                          target_tokens: List[str],
                          doc_tokens: List[str],
                          topn: int = 10) -> float:
    """ The function defines the similarity of a single word to a document,
    as the average of its similarity with the top_n most similar words in that document.
    To calculate the similarity score it calculates the similarity of every word in the target_tokens set with all the words in the doc_tokens,
    and keeps the top_n highest scores for each word and then averages over all the kept scores.
    -----
    Parameters:
    target_tokens List[str] : A list of sentiment or opinion words that indicate negative or positive opinions

    doc_tokens List[str]    : A tokenized document

    keyed_vectors           : A word2vec vocabulary model

    topn (int)              : An int that indicates the number of
    most similar vectors used to calculate the similarity score.

    Returns:
    vector similarity scores between 2 tokenized list doc_tokens and target_tokens
    """
    topn = min(topn, round(len(doc_tokens)))

    target_tokens = [token for token in target_tokens if token in keyed_vectors]

    doc_tokens = [token for token in doc_tokens if token in keyed_vectors]

    sim_matrix = list_similarity(keyed_vectors=keyed_vectors,
                                 wordlist1=target_tokens,
                                 wordlist2=doc_tokens)
    sim_matrix = np.sort(sim_matrix, axis=1)[:, -topn:]

    similarity_score = np.mean(sim_matrix)

    return similarity_score

def calculate_similarity_score(keyed_vectors,
                          target_tokens: List[str],
                          doc_tokens: List[str],
                          topn: int = 10) -> float:
    """ The function defines the similarity of a single word to a document,
    as the average of its similarity with the top_n most similar words in that document.
    To calculate the similarity score it calculates the similarity of every word in the target_tokens set with all the words in the doc_tokens,
    and keeps the top_n highest scores for each word and then averages over all the kept scores.
    -----
    Parameters:
    target_tokens List[str] : A list of sentiment or opinion words that indicate negative or positive opinions

    doc_tokens List[str]    : A tokenized document

    keyed_vectors           : A word2vec vocabulary model

    topn (int)              : An int that indicates the number of
    most similar vectors used to calculate the similarity score.

    Returns:
    vector similarity scores between 2 tokenized list doc_tokens and target_tokens
    """
    topn = min(topn, round(len(doc_tokens)))

    target_tokens = [token for token in target_tokens if token in keyed_vectors]

    doc_tokens = [token for token in doc_tokens if token in keyed_vectors]

    sim_matrix = list_similarity(keyed_vectors=keyed_vectors,
                                 wordlist1=target_tokens,
                                 wordlist2=doc_tokens)
    sim_matrix = np.sort(sim_matrix, axis=1)[:, -topn:]

    similarity_score = np.mean(sim_matrix)

    return similarity_score




def topn_semantic_sentiment_analysis(keyed_vectors,
                                      positive_target_tokens: List[str],
                                      negative_target_tokens: List[str],
                                      spam_target_tokens: List[str],
                                      doc_tokens: List[str],
                                      topn: int = 10) -> float:
    """
    A function to calculate the semantic sentiment of the text by measuring vector similarity between
    doc_tokens and a positive_target_tokens (as positive_score) then measuring vector similarity between
    doc_tokens and a negative_target_tokens (as negative_score), and finally comparing these two scores.

    Parameters:
    keyed_vectors           : A word2vec vocabulary model
    positive_target_tokens  : A list of sentiment or opinion words that indicate positive opinions
    negative_target_tokens  : A list of sentiment or opinion words that indicate negative opinions
    doc_tokens              : A tokenized document


    Returns:
    positive_score            : vector similarity scores between doc_tokens and positive_target_tokens
    negative_score            : vector similarity scores between doc_tokens and negative_target_tokens

    semantic_sentiment_score  : positive_score - negative_score
    semantic_sentiment_polarity       : Overall score: 0 for more negative or 1 for more positive doc
    """

    positive_score = doc_tokens.apply(lambda x: calculate_topn_similarity_score(keyed_vectors=keyed_vectors,
                                                                 target_tokens=positive_target_tokens,
                                                                 doc_tokens=x,
                                                                     topn=topn))
    print("Positive scores completed.")
    negative_score = doc_tokens.apply(lambda x: calculate_topn_similarity_score(keyed_vectors=keyed_vectors,
                                                                 target_tokens=negative_target_tokens,
                                                                 doc_tokens=x,
                                                                     topn=topn))
    print("Negative scores completed.")
    spam_score = doc_tokens.apply(lambda x: calculate_topn_similarity_score(keyed_vectors=keyed_vectors,
                                                                 target_tokens=spam_target_tokens,
                                                                 doc_tokens=x,
                                                                     topn=topn))
    print("Spam scores completed.")
    semantic_sentiment_score = positive_score - negative_score

    #semantic_sentiment_polarity = semantic_sentiment_score.apply(lambda x: 1 if (x > 0) else 0)

    return positive_score, negative_score, semantic_sentiment_score, spam_score


def scale(x, srcRange, dstRange):
    ''' A function to scale sentiment to a desired range.
    Parameters:
    x           : A value to scale
    srcRange:   : Source range (min, max)
    dstRange    : Desired range to scale to (min, max)

    Returns:
    A scaled value of X
    '''
    return (x-srcRange[0])*(dstRange[1]-dstRange[0])/(srcRange[1]-srcRange[0])+dstRange[0]
