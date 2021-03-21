import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import configparser
from sql_queries import db_config_queries,db_tables_ddl

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read("settings.cfg")
    #Get Database credentials
    host_cfg = config.get('postgres_Database_Credentials', 'host')
    database_cfg = config.get('postgres_Database_Credentials', 'database')
    user_cfg = config.get('postgres_Database_Credentials', 'user')
    pswrd_cfg = config.get('postgres_Database_Credentials', 'password')

    #Connect to DB
    try:
        conn = psycopg2.connect(
            host=host_cfg,
            database=database_cfg,
            user=user_cfg,
            password=pswrd_cfg)

    except psycopg2.DatabaseError as err:
        print(err)

    cur = conn.cursor()
    conn.set_session(autocommit=True)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    #Run configuration queries
    for query in db_config_queries:
        cur.execute(query)

    # Get the new Database credentials
    host_cfg = config.get('youtubeapi_Database_Credentials', 'host')
    database_cfg = config.get('youtubeapi_Database_Credentials', 'database')
    user_cfg = config.get('youtubeapi_Database_Credentials', 'user')
    pswrd_cfg = config.get('youtubeapi_Database_Credentials', 'password')

    # Connect to the new DB
    try:
        conn = psycopg2.connect(
            host=host_cfg,
            database=database_cfg,
            user=user_cfg,
            password=pswrd_cfg)
        print('ok')
    except psycopg2.DatabaseError as err:
        print(err)

    cur = conn.cursor()
    conn.set_session(autocommit=True)

    # Create tables
    for query in db_tables_ddl:
        cur.execute(query)
        conn.commit()

    conn.close()