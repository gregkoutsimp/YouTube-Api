# from  api_pck.functions import YoutubeApi
from apscheduler.schedulers.blocking import BlockingScheduler
from api_pck.youtubeapi  import YoutubeApi,  insert_values_tables
import psycopg2
import pandas as pd
import datetime as dt
import configparser
from sql_queries import details_table_insert
from time import time
import schedule


def main():
    l_details= []

    config = configparser.ConfigParser()
    config.read("settings.cfg")

    host_cfg = config.get('youtubeapi_Database_Credentials', 'host')
    database_cfg = config.get('youtubeapi_Database_Credentials', 'database')
    user_cfg = config.get('youtubeapi_Database_Credentials', 'user')
    pswrd_cfg = config.get('youtubeapi_Database_Credentials', 'password')
    try:
        conn = psycopg2.connect(
            host=host_cfg,
            database=database_cfg,
            user=user_cfg,
            password=pswrd_cfg)
    except psycopg2.DatabaseError as err:
        print(err)
    cur = conn.cursor()
    cur.execute("SELECT video_id FROM videos")
    videoid_rec = cur.fetchall()

    youtubeclass = YoutubeApi()

    for id in videoid_rec:
        d = youtubeclass.get_video_details(id[0])

        # print(id[0])

        l_details.append(d)

    df_details = pd.DataFrame(l_details)

    df_details[['views', 'likes','dislikes']] = df_details[['views', 'likes','dislikes']].astype(int)

    df_details= df_details[['id','views','likes', 'dislikes']]

    df_details['date_time'] = dt.datetime.now()

    insert_values_tables(df_details,details_table_insert, cur, conn)

    conn.close()


if __name__ == '__main__':
    start = time()
    # sched = BlockingScheduler()
    #
    # # Schedule job_function to be called every two hours
    # sched.add_job(main, 'interval', hours=1, start_date=dt.datetime.now(),
    #               end_date=dt.datetime.now() + dt.timedelta(hours=48))
    # try:
    #     sched.start()
    # except KeyboardInterrupt:
    #     print('Terminating...')
    main()

    end = time()
    elapsed = (end - start) / 60
    print('***************************')
    print('\n Elapsed time (minutes):', elapsed)
    print('***************************')

