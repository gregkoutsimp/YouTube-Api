import configparser
from apiclient.discovery import build
import re
from youtube_transcript_api import YouTubeTranscriptApi


class YoutubeApi:
    """

    Retrieves video meta-data and videos subtitles based on the user input
    """


    # Get credentials
    config = configparser.ConfigParser()
    config.read("settings.cfg")

    api_key = config.get('Api_Settings', 'api_key')
    api_service_name = config.get('Api_Settings', 'api_service_name')
    api_version = config.get('Api_Settings', 'api_version')
    # Create an Api Client
    youtube = build(api_service_name, api_version, developerKey=api_key)
    # Video Url prefix, conacat with videoId
    url_prefix = 'https://www.youtube.com/watch?v='
    # List of words that exlude videos
    l_exclude = ['compilations', 'compilation', 'episodes', 'moments']
    # Apply the sufix to user input for a more accurate search result
    search_suffix = ' cartoon with english subtitles'

    def __init__(self):

        self.titles_url_ll = []
        self.l_dpl = []
        self.videos_subtitle_l = []

    def parseInt(self, string):
        return int(''.join([x for x in string if x.isdigit()]))

    def YTDurationToSeconds(self, duration):
        match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
        hours = self.parseInt(match[0]) if match[0] else 0
        minutes = self.parseInt(match[1]) if match[1] else 0
        seconds = self.parseInt(match[2]) if match[2] else 0
        # Get details per video and turn duration to sec
        return (hours * 3600 + minutes * 60 + seconds)

    def get_video_details(self, video_id):
        vi = {}
        request = YoutubeApi.youtube.videos().list(
            part="contentDetails,statistics",
            id=video_id
        )
        response = request.execute()

        try:
            vi['id'] = video_id
            vi['duration_sec'] = self.YTDurationToSeconds(response['items'][0]['contentDetails']['duration'])
            vi['views'] = response['items'][0]['statistics']['viewCount']
            vi['likes'] = response['items'][0]['statistics']['likeCount']
            vi['dislikes'] = response['items'][0]['statistics']['dislikeCount']

        except BaseException:
            vi['likes'] = '0'
            vi['dislikes'] = '0'

        return vi

    # Checks if video exists and language is en
    # Both auto an manually generated
    # Will append to list of dict in or out of func?
    def get_video_cc(self, video_id, languages='en'):  # enclosed captions are rejected
        error_flag = 0
        d_cc = {}

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript([languages])
            trans_fetch = transcript.fetch()

            # from all text remove () and [] with spaces
            str_list = [i for i in trans_fetch if re.sub("[\(\[].*?[\)\]]", "", i['text']) != ""]

            # Count phrases before removal
            raw_list_size = len(trans_fetch)

            # total sub duration avoiding overlapping
            total_sub_dur = 0
            for index in range(1, len(str_list)):
                if (str_list[index]['start'] - str_list[index - 1]['start']) < str_list[index - 1]['duration']:
                    total_sub_dur += (str_list[index]['start'] - str_list[index - 1]['start'])
                else:
                    total_sub_dur += str_list[index - 1]['duration']

            # Count phrases after removal
            phrase_cnt = len(str_list)

            # percentage diff of subs after cleaned
            diff = 100 * (phrase_cnt - raw_list_size) / raw_list_size

            # concat all text from cleaned subs
            total_subs = ' '.join(line['text'] for line in str_list)

            d_cc['VideoId'] = video_id,
            d_cc['subs'] = total_subs
            d_cc['subs_removed_%'] = round(abs(diff))
            d_cc['total_sub_duration'] = round(total_sub_dur)

            return error_flag, d_cc

        except:
            error_flag = 1
            return error_flag, {}

    def search_videos_from_playlists(self, playlist_id, max_results=50, token=None):
        reqPlaylist = YoutubeApi.youtube.playlistItems().list(playlistId=playlist_id, part='snippet',
                                                              maxResults=max_results,
                                                              pageToken=token)
        resPlaylist = reqPlaylist.execute()

        try:
            nexttok = resPlaylist["nextPageToken"]
        except Exception as e:
            nexttok = "last_page"

        return nexttok, resPlaylist['items']

    def get_playlist_videos(self, playlist_id, search_input, token=None, cnt_pl_vid=0):

        # Split user input
        split_search = re.findall(r"[\w']+", search_input.lower())

        all_playlist_vid = self.search_videos_from_playlists(playlist_id, token=token)
        token = all_playlist_vid[0]
        videos = all_playlist_vid[1]

        # Iterate for all the results
        for vid in videos:
            di = {}
            d_subs = {}
            # Split the video title
            split_title = re.findall(r"[\w']+", vid['snippet']['title'].lower())

            subs = self.get_video_cc(vid['snippet']['resourceId']['videoId'])
            subs_error = subs[0]
            subs_dict = subs[1]

            if cnt_pl_vid < 100:  # Counter reserves that only 100 valid videos  per playlist
                # Conditions for accepting or rejecting a video
                if (any(x in split_title for x in split_search) and  # at least on word from user input in video title
                        bool(re.search(r'\d{4}[-,_,/,\,:]\d{4}',
                                       vid['snippet']['title'])) == False and  # Checks for pattern YYYY[-,_,/,\,:]YYYY
                        bool(re.search(r'part \d+[-,_,/,\,:]\d+',
                                       vid['snippet']['title'])) == False and  # Checks for pattern part00[-,_,/,\,:]00
                        any(x in split_title for x in
                            YoutubeApi.l_exclude) == False and  # No excluded word in video title
                        subs_error == 0):  # English subs exists

                    video_details = self.get_video_details(vid['snippet']['resourceId']['videoId'])

                    # Calculate the percentage of video duration that is subtitled
                    duration_metric = subs_dict['total_sub_duration'] / video_details['duration_sec']

                    # Percentage of removed subtitles
                    nbr_phrase_metric = subs_dict['subs_removed_%']

                    if (duration_metric > 0.5 and  # condition for sub quality according time
                            nbr_phrase_metric < 30):  # condition for sub quality

                        # Counter for accepted videos
                        cnt_pl_vid += 1

                        # Gather video Info
                        di['videoId'] = vid['snippet']['resourceId']['videoId']
                        di['title'] = vid['snippet']['title']
                        di['url'] = YoutubeApi.url_prefix + vid['snippet']['resourceId']['videoId']
                        di['duration'] = video_details['duration_sec']
                        di['views'] = video_details['views']
                        di['likes'] = video_details['likes']
                        di['dislikes'] = video_details['dislikes']
                        self.titles_url_ll.append(di)

                        dpl = {}
                        dpl['playlistId'] = playlist_id
                        dpl['videoId'] = vid['snippet']['resourceId']['videoId']
                        self.l_dpl.append(dpl)

                        # Gather video subtitle
                        d_subs['videoId'] = vid['snippet']['resourceId']['videoId']
                        d_subs['subs'] = subs_dict['subs']
                        d_subs['phrase_metric'] = nbr_phrase_metric
                        self.videos_subtitle_l.append(d_subs)
            else:
                break  # Break when reach 100 video per playlist

        return token, cnt_pl_vid

    def playlist_vid(self, playlist_id, search_input):

        var = self.get_playlist_videos(playlist_id, search_input)
        token = var[0]

        nbr_of_accepted_vid = var[1]

        while token != 'last_page' and nbr_of_accepted_vid < 100:  # Counter reserves that only 100 valid videos pers playlist
            var = self.get_playlist_videos(playlist_id, search_input, token=token, cnt_pl_vid=nbr_of_accepted_vid)
            token = var[0]
            nbr_of_accepted_vid += var[1]

        return nbr_of_accepted_vid

    def youtube_search(self, search_input, max_results=50, token=None):

        search_str = search_input + YoutubeApi.search_suffix
        req = YoutubeApi.youtube.search().list(q=search_str, part="snippet", maxResults=max_results, pageToken=token)
        res = req.execute()

        try:
            nexttok = res["nextPageToken"]
        except Exception as e:
            nexttok = "last_page"

        return nexttok, res['items']

    def get_search_results(self, search_input, token=None, total_res=0, pl_cnt=0, vd_cnt=0,
                           total_nbr_of_accepted_pl_vid=0):
        all_res = self.youtube_search(search_input, token=token)
        token = all_res[0]
        results = all_res[1]

        # Split user input
        split_search = re.findall(r"[\w']+", search_input.lower())

        # Iterate for all the results
        for res in results:
            di = {}
            d_subs = {}

            # Split video title
            split_title = re.findall(r"[\w']+", res['snippet']['title'].lower())

            if total_res < 100:  # Counter reserves  100 valid results
                if res['id']['kind'] == 'youtube#video':  # for video results

                    subs = self.get_video_cc(res['id']['videoId'])
                    subs_error = subs[0]
                    subs_dict = subs[1]

                    if (any(x in split_title for x in
                            split_search) and  # at least on word from user input in video title
                            bool(re.search(r'\d{4}[-,_,/,\,:]\d{4}', res['snippet'][
                                'title'])) == False and  # Checks for pattern YYYY[-,_,/,\,:]YYYY
                            bool(re.search(r'part \d+[-,_,/,\,:]\d+', res['snippet'][
                                'title'])) == False and  # Checks for pattern part00[-,_,/,\,:]00
                            any(x in split_title for x in
                                YoutubeApi.l_exclude) == False and  # No exluded word in video title
                            subs_error == 0):  # English subs exists

                        video_details = self.get_video_details(res['id']['videoId'])

                        # #Calculate the percentage of video duration that is subtitled
                        duration_metric = subs_dict['total_sub_duration'] / video_details['duration_sec']

                        # Percentage of removed subtitles
                        nbr_phrase_metric = subs_dict['subs_removed_%']

                        if (duration_metric > 0.5 and  # condition for sub quality according time
                                nbr_phrase_metric < 30):  # condition for sub quality

                            vd_cnt += 1  # counter of videos used
                            total_res += 1  # Counter of total accepted results

                            # Gather Video Info
                            di['videoId'] = res['id']['videoId']
                            di['title'] = res['snippet']['title']
                            di['url'] = YoutubeApi.url_prefix + res['id']['videoId']
                            di['duration'] = video_details['duration_sec']
                            di['views'] = video_details['views']
                            di['likes'] = video_details['likes']
                            di['dislikes'] = video_details['dislikes']
                            self.titles_url_ll.append(di)

                            d_subs['videoId'] = res['id']['videoId']
                            d_subs['subs'] = subs_dict['subs']
                            d_subs['phrase_metric'] = nbr_phrase_metric
                            self.videos_subtitle_l.append(d_subs)

                elif res['id']['kind'] == 'youtube#playlist' and pl_cnt < 3:  # for playlits results ensuring only 3 playlist will be accepted

                    playlistId = res['id']['playlistId']

                    nbr_of_accepted_pl_vid = self.playlist_vid(playlistId, search_input)
                    # total_nbr_of_accepted_pl_vid += nbr_of_accepted_pl_vid

                    if nbr_of_accepted_pl_vid > 0:  # Cout only playlists with valid videos
                        pl_cnt += 1
                        total_res += 1

                else:  # continue if not video or playlist
                    continue
            else:  # Break when reach 100 valid results
                break

        return token, pl_cnt, vd_cnt, total_res

    def final(self, search_input):
        """

        :param search_input: Cartoon name
        :return: video details and videos subtitles lists of dictionaries
        """

        self.search_input = search_input

        # Call search results for default parameters
        search_res = self.get_search_results(search_input)
        token = search_res[0]  # next page token
        used_playlists = search_res[1]  # number of used playlists, max value must be 3
        used_video = search_res[2]  # counter for used video
        total_of_all = search_res[3]  # total accepted results counter

        # print(len(self.titles_url_ll), total_of_all, used_video, used_playlists)

        # Iterate for all result pages until reach required valid number
        while token != 'last_page' and total_of_all < 100:  # Counter reserves  only 100 valid results
            # #Call search results with parameters of previous results
            search_res = self.get_search_results(search_input, token=token, total_res=total_of_all,
                                                 pl_cnt=used_playlists)
            token = search_res[0]
            total_of_all = search_res[3]

            if used_playlists < 3:
                used_playlists += search_res[1]

            used_video += search_res[2]
            print(len(self.titles_url_ll), total_of_all, used_video, used_playlists)
        return self.titles_url_ll, self.videos_subtitle_l


def insert_values_tables(df, insert_stmn, cur, conn):
    """

    :param df: DataFrame
    :param insert_stmn: SQL insert statement
    :param cur: database connection cursor
    :param conn: database connection
    """
    for i in df.values.tolist():
        cur.execute(insert_stmn, i)
    conn.commit()
