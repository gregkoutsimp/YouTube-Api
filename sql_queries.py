import configparser

config = configparser.ConfigParser()
config.read("settings.cfg")

youtube_api_db = config.get('youtubeapi_Database_Credentials', 'database')
youtube_api_user = config.get('youtubeapi_Database_Credentials', 'user')
youtube_api_passwd = config.get('youtubeapi_Database_Credentials', 'password')

#DROP DATABASE
drop_db = "DROP DATABASE IF EXISTS {};".format(youtube_api_db)

#CREATE DATABASE
create_database = "CREATE DATABASE {} WITH ENCODING 'utf8' TEMPLATE template0;".format(youtube_api_db)


#DROP USER
drop_user = "DROP USER IF EXISTS {};".format(youtube_api_user)


#CREATE USER
create_user = "CREATE ROLE {} LOGIN SUPERUSER PASSWORD '{}' CREATEDB CREATEROLE INHERIT ;".format(youtube_api_user, youtube_api_passwd)
grant_user = "GRANT ALL PRIVILEGES ON DATABASE {} TO {};".format(youtube_api_db, youtube_api_user)


#DROP TABLES
# video_table_drop = 'DROP TABLE IF EXISTS videos;'
# details_table_drop = 'DROP TABLE IF EXISTS video_details;'

#CREATE TABLES
video_table_create = """
CREATE TABLE videos (
    
    VIDEO_ID VARCHAR(1000) PRIMARY KEY NOT NULL
    ,TITLE VARCHAR(1000)
    ,URL VARCHAR(1000)
    ,DURATION INT
    ,VIEW INT
    ,LIKES INT
    ,DISLIKES INT
    ,PHRASE_METRIC INT
    ,CI float)
"""

details_table_create = """
CREATE TABLE video_details (
    id SERIAL PRIMARY KEY
    ,VIDEO_ID VARCHAR(1000) 
    ,VIEWS INT
    ,LIKES INT
    ,DISLIKES INT
    ,DATE_TIME TIMESTAMP)
"""


#INSERT INTO TABLES
video_table_insert = "INSERT INTO videos VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (video_id) DO NOTHING"

details_table_insert = "INSERT INTO video_details (VIDEO_ID,VIEW,LIKES,DISLIKES,DATE_TIME) VALUES (%s,%s,%s,%s,%s)"

#LIST OF QUERIES
db_config_queries = [drop_db, create_database, drop_user, create_user, grant_user]

db_tables_ddl = [video_table_create,  details_table_create]


