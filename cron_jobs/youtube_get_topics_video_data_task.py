#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from googleapiclient.discovery import build # google official library
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json, pytz, gspread, gspread, os, base64

load_dotenv()

#**** Global variables ****
API_KEY = os.getenv('API_KEY')
GOOGLE_SHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_JSON_B64 = os.getenv('GOOGLE_SHEET_JSON_B64')
GOOGLE_SHEET_SERVICE_ACCOUNT_FILE='google-sheet-key.json'
YOUTUBE_SPREADSHEET_ID = os.getenv('YOUTUBE_SPREADSHEET_ID')
YOUTUBE_SEARCH_FILM_WORKSHEET_NAME = 'Search_film_list'
LOGS_WORKSHEET_NAME = 'Logs'

#**** Classes ****
class Youtube_video:
    def __init__(self, id:str, title:str, description:str):
        self.id = id
        self.title = title
        self.description = description
class Topic:
    def __init__(self, name: str, keywords: list, youtube_videos: list = []):
        self.name = name
        self.keywords = keywords
        self.youtube_videos = youtube_videos
    def add_youtube_videos(self, youtube_videos: list):
        self.youtube_videos.extend(youtube_videos)
        
#**** Functions ****
# Time related functions
def format_date_to_utc(dt):
    return dt.strftime("%Y-%m-%dT16:00:00Z")
def get_previous_month_range_in_utc():
    # 設定台灣時區 (+8)
    taiwan_tz = pytz.timezone('Asia/Taipei')
    
    # 今天的日期
    today = datetime.today()
    
    # 台灣時區轉換
    today_taiwan = taiwan_tz.localize(today)
    
    # 本月的第一天
    first_day_this_month = today_taiwan.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 上個月的最後一天 = 本月的第一天 - 1 天
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    
    # 上個月的第一天
    first_day_prev_month = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 轉換成 UTC
    utc_first_day = first_day_prev_month.astimezone(pytz.utc)
    utc_last_day = last_day_prev_month.astimezone(pytz.utc)
    
    return format_date_to_utc(utc_first_day), format_date_to_utc(utc_last_day)

def get_now_time_string():
    # 獲取當前時間
    now = datetime.now()
    
    # 設定時區，例如 Asia/Taipei
    timezone = pytz.timezone("Asia/Taipei")
    localized_time = now.astimezone(timezone)
    
    # 格式化時間為 yyyy-MM-dd HH:mm:ss+時區
    formatted_time = localized_time.strftime("%Y-%m-%d %H:%M:%S%z")
    return formatted_time

def log_youtube_info(function_name:str, query_string:str, process_result:str):
    update_google_sheet_column(
        sheet_id = YOUTUBE_SPREADSHEET_ID,
        worksheet_name = LOGS_WORKSHEET_NAME,
        search_column_number = 0,
        search_keyword = function_name,
        update_column =  'B',
        update_content = f'[query:{query_string}]{process_result}'
    )
    update_google_sheet_column(
        sheet_id = YOUTUBE_SPREADSHEET_ID,
        worksheet_name = LOGS_WORKSHEET_NAME,
        search_column_number = 0,
        search_keyword = function_name,
        update_column =  'C',
        update_content = get_now_time_string()
    )
    
def log_youtube_error(exception: Exception, function_name:str, query_string:str):
    error_status = exception.resp.status
    error_content = exception.content.decode("utf-8") if hasattr(exception.content, 'decode') else str(exception.content)
    # print(f"[ERROR] HTTP {error_status}")
    # print(error_content)
    update_google_sheet_column(
        sheet_id = YOUTUBE_SPREADSHEET_ID,
        worksheet_name = LOGS_WORKSHEET_NAME,
        search_column_number = 0,
        search_keyword = function_name,
        update_column =  'B',
        update_content = f'[query:{query_string}][ERROR] HTTP {error_status}, {error_content}'
    )
    update_google_sheet_column(
        sheet_id = YOUTUBE_SPREADSHEET_ID,
        worksheet_name = LOGS_WORKSHEET_NAME,
        search_column_number = 0,
        search_keyword = function_name,
        update_column =  'C',
        update_content = get_now_time_string()
    )
    
# Youtube related functions
def get_youtube_service():
    return build('youtube', 'v3', developerKey=API_KEY)
def youtube_search(query, start_utc_datetime, end_utc_datetime):
    service = get_youtube_service()
    try:
        search_response = service.search().list(
            part='snippet',
            maxResults=50,
            order='relevance',
            publishedAfter=start_utc_datetime,
            publishedBefore=end_utc_datetime,
            q=query,
            regionCode='TW',
            relevanceLanguage='zh',
            type='video'
        ).execute()
        # print(json.dumps(search_response, indent=2, ensure_ascii=False))
    except HttpError as e:
        log_youtube_error(
            exception = e, 
            function_name = YOUTUBE_SEARCH_FILM_WORKSHEET_NAME, 
            query_string= query
        )
        return None
        
    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append(Youtube_video(
                id=search_result['id']['videoId'], 
                title=search_result['snippet']['title'], 
                description=search_result['snippet']['description']))
    log_youtube_info(
        function_name = YOUTUBE_SEARCH_FILM_WORKSHEET_NAME,
        query_string = query,
        process_result = f'Successfully searched.'
    )
    return videos    
# google sheet related
def write_secret_json():
    with open(GOOGLE_SHEET_SERVICE_ACCOUNT_FILE, 'wb') as f:
        f.write(base64.b64decode(GOOGLE_SHEET_JSON_B64))
def delete_secret_json():
    if os.path.exists(GOOGLE_SHEET_SERVICE_ACCOUNT_FILE):
        os.remove(GOOGLE_SHEET_SERVICE_ACCOUNT_FILE)
def get_google_sheet_service():
    creds = Credentials.from_service_account_file(
        GOOGLE_SHEET_SERVICE_ACCOUNT_FILE, scopes=GOOGLE_SHEET_SCOPES
    )
    return build('sheets', 'v4', credentials=creds)
def update_full_google_sheet(sheet_id:str, worksheet_name:str, update_rows: list):
    service = get_google_sheet_service()
    # clear old data
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=worksheet_name,
        body={}
    ).execute()    
    # update data
    body = {
        'values': update_rows
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=YOUTUBE_SPREADSHEET_ID, range=worksheet_name,
        valueInputOption="RAW", body=body).execute()
    print(f"{result.get('updatedCells')} cells updated.")

def update_google_sheet_column(sheet_id:str, worksheet_name:str, search_column_number:int, search_keyword:str, update_column:str, update_content:str):
    service = get_google_sheet_service()    
    # open worksheet
    sheet = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=worksheet_name).execute()
    values = sheet.get('values', [])
    if not values:
        print('worksheet not found.')
        return  
        
    for i, row in enumerate(values):
        if len(row) > 0 and row[search_column_number] == search_keyword:
            row_index = i + 1
            update_body = {
                'values': [[update_content]]
            }
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'{worksheet_name}!{update_column}{row_index}',
                valueInputOption='RAW',
                body=update_body
            ).execute()
            print(f'{search_keyword} result was updated')
            break

#### collect youtube video data ###
write_secret_json()
try:
    # search youtube film
    start_utc_datetime, end_utc_datetime = get_previous_month_range_in_utc()
    topics = [
        Topic('心理議題', ['心理學', '自我成長', '心情', '感情']),
        Topic('社會弱勢議題', ['社會弱勢', '經濟弱勢', '社會不平等']),
        Topic('社會議題', ['社會議題', '社會問題']),
        Topic('科技議題', ['AI', '科技']),
    ]
    for topic in topics:
        for keyword in topic.keywords:
            videos = youtube_search(keyword, start_utc_datetime, end_utc_datetime)
            if videos is None:
                print('search youtube file fail.')
                break
            topic.add_youtube_videos(videos)
    
    # transform original data to table
    update_rows = [["主題", "搜尋關鍵字", "影片ID", "影片標題", "影片描述"]]
    for topic in topics:
        keywords_string = '、'.join(topic.keywords)
        for video in topic.youtube_videos:
            update_rows.append([
                topic.name,
                keywords_string,
                video.id,
                video.title,
                video.description
            ])
    # update google sheet
    update_full_google_sheet(
        sheet_id = YOUTUBE_SPREADSHEET_ID,
        worksheet_name = YOUTUBE_SEARCH_FILM_WORKSHEET_NAME,
        update_rows = update_rows
    )
finally:
    delete_secret_json()


# In[ ]:




