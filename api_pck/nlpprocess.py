from textblob import TextBlob
from textblob import Blobber
from textblob.sentiments import NaiveBayesAnalyzer
import nltk
from nltk.corpus import stopwords
import en_core_web_sm
import string
import pandas as pd
import numpy as np


def lemmatization_process(nlp, sub):
    """

    :param nlp: nlp model
    :param sub: text to precess
    :return:
    """
    doc = nlp(sub)
    return " ".join([token.lemma_ for token in doc])


def nlp_process(titles_url_ll, videos_subtitle_l):
    """

    :param titles_url_ll: videos list of dictionaries
    :param videos_subtitle_l: subtitles list of dictionaries
    :return: Dataframe with metrics
    """
    df_titles = pd.DataFrame(titles_url_ll).drop_duplicates()  # some videos in playlists and alone also
    df_subs = pd.DataFrame(videos_subtitle_l).drop_duplicates()

    tb = Blobber(analyzer=NaiveBayesAnalyzer())
    nlp = en_core_web_sm.load(disable=['parser', 'ner'])

    # turn text to lowercase
    df_subs['proc_subs'] = df_subs['subs'].apply(lambda x: " ".join(x.lower() for x in x.split()))

    # remove punctuation
    punct = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{}~'  # `|` is not present here
    transtab = str.maketrans(dict.fromkeys(punct, ''))

    df_subs['proc_subs'] = '|'.join(df_subs['proc_subs'].tolist()).translate(transtab).split('|')

    # remove stop words
    stop = stopwords.words('english')
    df_subs['proc_subs'] = df_subs['proc_subs'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))

    # lemmatization
    df_subs['proc_subs'] = np.vectorize(lemmatization_process)(nlp, df_subs['proc_subs'])

    df_subs['patternAnalyzer'] = df_subs['proc_subs'].apply(lambda x: TextBlob(x).sentiment.polarity)
    df_subs['NaiveBayesAnalyzer'] = df_subs['proc_subs'].apply(lambda x: tb(x).sentiment.p_pos)
    df_subs['patternAnalyzerScaled'] = df_subs['patternAnalyzer'] - df_subs['patternAnalyzer'].min() / (
                df_subs['patternAnalyzer'].max() - df_subs['patternAnalyzer'].min())
    df_subs['Composite Index'] = (df_subs['patternAnalyzerScaled'] + df_subs['NaiveBayesAnalyzer']) / 2

    df_analyzer = df_subs[['videoId', 'phrase_metric', 'Composite Index']]

    df_total = df_titles.merge(df_analyzer, on='videoId', how='left')  # Change columns to int

    df_total[['views', 'likes', 'dislikes']] = df_total[['views', 'likes', 'dislikes']].astype(int)
    df_total['Composite Index'] = round(df_total['Composite Index'].astype(float), 2)

    return df_total
