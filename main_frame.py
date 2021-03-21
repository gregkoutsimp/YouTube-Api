from api_pck.youtubeapi import YoutubeApi, insert_values_tables
from api_pck.nlpprocess import  nlp_process
import configparser
import psycopg2
import pandas as pd
from sql_queries import video_table_insert
from time import time

if __name__ == '__main__':
    start = time()

    # Get the credentials for the db
    config = configparser.ConfigParser()
    config.read("settings.cfg")

    host_cfg = config.get('youtubeapi_Database_Credentials', 'host')
    database_cfg = config.get('youtubeapi_Database_Credentials', 'database')
    user_cfg = config.get('youtubeapi_Database_Credentials', 'user')
    pswrd_cfg = config.get('youtubeapi_Database_Credentials', 'password')

    # Search value given by user
    user_input = input('Enter cartoon name: ')
    # Call the YoutubeApi class
    youtubeclass = YoutubeApi()
    # Get the results of the class
    titles_url, videos_subtitle = youtubeclass.final(user_input)

    # Create a df from list and calculating the sentiment content of the subs
    mydf = nlp_process(titles_url, videos_subtitle)

    # Connect to DB
    try:
        conn = psycopg2.connect(
            host=host_cfg,
            database=database_cfg,
            user=user_cfg,
            password=pswrd_cfg)
    except psycopg2.DatabaseError as err:
        print(err)
    # Open the cursor for the db
    cur = conn.cursor()

    # Insert results into db
    #  Write to db
    insert_values_tables(mydf, video_table_insert, cur, conn)

    #  Close connection
    cur = conn.close()

    end = time()

    elapsed = (end - start) / 60
    print('***************************')
    print('\n Elapsed time (minutes):', elapsed)
    print('***************************')






