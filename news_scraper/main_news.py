import os
from datetime import datetime, timedelta
import json
import re

FILENAME = "bulk.json"
CHUNK = "temp.json"
MINIMUM_BATCH = 5

def utf8_to_ascii(s:str, ws=re.compile('\s+', flags=re.M)) -> str:
    s = s.encode("utf8")
    s = s.decode("ascii", errors="replace")
    s = s.replace(u"\ufffd", " ")
    s = ws.sub(" ", s)
    return s.strip()

def reset_bulkfile(filename:str):
    # reset bulk
    bulk = open(filename, "w+")
    bulk.write("")
    bulk.close

def get_spider_list(path: str) -> list:
    os.system(f"cd {path} && scrapy list > spider_list.txt")
    spider_list = []
    with open(f"{path}spider_list.txt", "r") as file:
        for spider in file:
            spider_list.append(spider.rstrip())
    return spider_list

def scrap(path:str ="./"):
    temp_path_abs = path.rstrip("/") + "/temp/"
    temp_path_dyn = "temp/"
    spider_list = get_spider_list(path)
    print("spider: ", spider_list)

    for spider in spider_list:
        filename_abs = temp_path_abs + spider + ".json"
        filename_dyn = temp_path_dyn + spider + ".json"
        print(f"crawling: {spider} to {filename_abs}")
        reset_bulkfile(filename_abs)

        os.system(
            f"cd {path} && scrapy crawl "
            + spider
            + " --nolog -o "
            + filename_dyn
            + " -a hourly=True"
        )

def serialize(path: str="./",):
    temp_path = path.rstrip("/") + "/temp/"
    spider_list = get_spider_list(path)

    docs=[]
    for spider in spider_list:
        filename = temp_path + spider + ".json"
        print(f"\nserializing: {spider} from {filename}")

        if os.stat(filename).st_size != 0:
            with open(filename) as f:
                data = json.load(f)

            len_data = len(data)
            try:
                print(f">>got {len_data} record(s)")
            except:
                pass

            for row in data:
                final_data = news_serialize(row)
                docs.append(final_data)
        elif  os.stat(filename).st_size == 0:
            continue
    return docs

def news_serialize(data:dict) -> dict:
    source = {
        'platform' : "News",
        'content': utf8_to_ascii(data['contentRaw']) if 'contentRaw' in data else None,
        'created_date' : data['createdAt'] if 'createdAt' in data else None,
        'date' : data['news_date'] if 'news_date' in data else None,                                
        'images' : (data['media'] if isinstance(data['media'],list) else [data['media']]) if 'media' in data else [],
        'media_source' : data['source'] if 'source' in data else None,                        
        'name': data['author'] if "author" in data and type(data['author']) == str else ", ".join(data['author']) if "author" in data and type(data['author']) == list else None,
        'news_category' : data['category'] if 'category' in data else None,
        'news_type' : data['type'] if 'type' in data else None,                        
        'url' :data['slug'] if 'slug' in data else None,
        'title' : data['title'] if 'title' in data else None,      
        'hashtags'  : data['tags'] if 'tags' in data else [],  
    }
    return source