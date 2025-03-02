import sys
import os

from .youtube_scraping_api import filter as yt_filter
from .youtube_scraping_api.__main__ import YoutubeAPI
from datetime import datetime, timedelta
import re

api = YoutubeAPI()
filter_by = yt_filter.SearchFilter(upload_date='today', sort_by="Upload date")

def text_preprocessing(text: str) -> str:
    text = re.sub("\n|\t|\r|\xa0|\u201d|\u201c|\u200b|\u2013|\u203c|\ufe0f", " ", text)
    text = re.sub(r"[^a-zA-z0-9.,!?/:;\"\'\s]", "", text)
    return text


def date_convert(date: str) -> str:
    try:
        if "Premiered" in date and "minutes" in date and "ago" in date:
            date_hours = date.split("Premiered ")[1]
            date_hours = date_hours.split(" ")[0]
            date_hours = int(date_hours) 
            date = datetime.now()-timedelta(minutes=date_hours)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "Premiered" in date and "ago" in date:
            date_hours = date.split("Premiered ")[1]
            date_hours = date_hours.split(" ")[0]
            date_hours = int(date_hours) 
            date = datetime.now()-timedelta(hours=date_hours)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "Streamed" in date and "ago" in date:
            date_hours = date.split("Streamed live ")[1]
            date_hours = date_hours.split(" ")[0]
            date_hours = int(date_hours) 
            date = datetime.now()-timedelta(hours=date_hours)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "Premiered" in date :            
            date = date.split("Premiered ")[1]
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            date = date + "T" + time_now
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            if date > datetime.now():
                date = date-timedelta(days=1)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "Streamed live on " in date:
            date = date.split("Streamed live on ")[1]
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            date = date + "T" + time_now
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            if date > datetime.now():
                date = date-timedelta(days=1)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "Streamed" in date:
            date = date.split("Streamed ")[1]
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            date = date + "T" + time_now
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            if date > datetime.now():
                date = date-timedelta(days=1)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        elif "live on" in date:
            date = date.split("live on ")[1]
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            date = date + "T" + time_now
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            if date > datetime.now():
                date = date-timedelta(days=1)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        else:
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")
            time_now = datetime.now().strftime("%H:%M:%S")
            date = date + "T" + time_now
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            # date = date+timedelta(hours=15)
            if date > datetime.now():
                date = date-timedelta(days=1)
            # date = date.isoformat()
            date = datetime.strftime(date, "%Y-%m-%dT%H:%M:%S")
        return date
    except Exception as e:
        print(e)
        date = (datetime.now()).isoformat()
        return date


def number_convert(number: str) -> int:
    try:
        if "." in number and len(re.split('(\d+)', number)[-2]) == 1:
            number = (
                number.replace(" rb", "00")
                .replace("K", "00")
                .replace(" jt", "00000")
                .replace("M", "00000")
                .replace(",", "")
                .replace(".", "")
            )
        elif "." in number and len(re.split('(\d+)', number)[-2]) == 2:
            number = (
                number.replace(" rb", "0")
                .replace("K", "0")
                .replace(" jt", "0000")
                .replace("M", "0000")
                .replace(",", "")
                .replace(".", "")
            )
        else:
            number = (
                number.replace(" rb", "000")
                .replace("K", "000")
                .replace(" jt", "000000")
                .replace("M", "000000")
                .replace(",", "")
                .replace(".", "")
            )
        return int(number)
    except:
        return None


def scrape_link(keyword: str) -> list:
        #SCRAPING PROCESS
        try:
            searchs = api.search(query=keyword, filter=filter_by)
        except:
            return []
        print(f"Scrap {keyword}: got {len(searchs)} videos")
        datas = []
        #SERIALIZE PROCESS
        for video in searchs:
            try:
                # print(keyword, video.id, video.title)
                data = scrape_video(video)
                datas.append(data)
            except Exception:
                continue
        print(f"Total scraped video from {keyword}: {len(datas)}")
        return datas

def scrape_video(video_id: object) -> dict:
    try:
        video = api.video(video_id.id)
        data = {}

        #TITLE
        title = str(video.title).title()
        
        #DESCRIPTION
        try:
            description = video._init_data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['attributedDescription']['content'].split("\n")[0]
        except:
            description = ""
        description = text_preprocessing(str(description))
        
        #CAPTION
        captions = video.captions
        if captions:
            if captions.get_caption("id"):
                # print("original")
                caption_eng = None
                caption = captions.get_caption("id").get_text()
            elif not captions.get_caption("id"):
                # print("translate")
                caption_eng = captions.get_caption().get_text()
                caption = captions.get_caption().translate_to("id").get_text()

            caption = caption.replace("\n", " ")
            description_ina = "{} [SUBTITLE] {}".format(description, caption)
            description_ina = description_ina.strip()
            description_ina = description_ina[:10000]

            description_raw = None
            if caption_eng:
                caption_eng = caption_eng.replace("\n", " ")
                description_raw = "{} [SUBTITLE] {}".format(description, caption_eng)
                description_raw = description_raw.strip()
                description_raw = description_raw[:10000]
        elif not captions:
            print(f">>Fail: https://www.youtube.com/watch?v={video.id} has no captions")
            return
        
        #LIKE COUNT
        data_count = video._init_data
        try:
            like_count = data_count['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['videoActions']['menuRenderer']['topLevelButtons'][0]['segmentedLikeDislikeButtonViewModel']['likeButtonViewModel']['likeButtonViewModel']['toggleButtonViewModel']['toggleButtonViewModel']['defaultButtonViewModel']['buttonViewModel']['title']
            like_count = number_convert(like_count)
        except Exception as e:
            print(e)
            like_count = None
        #COMMENT COUNT
        try:
            comment_count = video.getCommentCount()
            if not comment_count:
                comment_count = data_count['contents']['twoColumnWatchNextResults']['results']['results']['contents'][3]['itemSectionRenderer']['contents'][0]['commentsEntryPointHeaderRenderer']['commentCount']['simpleText']
            comment_count = number_convert(comment_count)
        except Exception as e:
            comment_count = None

        #SERIALIZE
        data["url"] = "https://www.youtube.com/watch?v=" + video.id
        data["title"] = title
        data["content"] = description_ina
        data["content_raw"] = description_raw
        data["created_date"] = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
        data["date"] = date_convert(video.publish_time)
        data["name"] = video.author.name
        data["user_id"] = video.author.id
        data["subscribers_count"] = number_convert(video.author.subscriber_count) if number_convert(video.author.subscriber_count) else None
        data["thumbnail"] = video.thumbnails.get("high", None)
        data["views_count"] = int(video.view_count)
        data["likes_count"] = like_count if type(like_count) == int else None
        data["unlikes_count"] = getattr(video, "unlike_count", None)
        data["comments_count"] = comment_count
        data["hashtags"] = video.tags if video.tags else []
        data["platform"] = "Youtube"
        data["post_id"] = video.id

        #data expiration handler
        week = datetime.now()-timedelta(days=7)
        if datetime.strptime(data['date'],"%Y-%m-%dT%H:%M:%S") < week:
            print(f">>Expired: {data['title']} | {data['post_id']} | {data['date']}")
            return 
        # print(video.publish_time)
        print(f">>Done: {data['title']} | {data['post_id']} | {data['date']}")
        return data
    except Exception as e:
        print(f">>Fail: {e}| https://www.youtube.com/watch?v={video.id}")
        return
    
def scrape(projects: list) -> list:
    docs = []
    for keyword in projects:
        print("Start Keyword :", keyword)
        data = scrape_link(keyword)
        if data:
            docs.extend(data)
        print("Finish Keyword :", keyword)
    print(f"Total scraped video: {len(docs)}")
    return docs
