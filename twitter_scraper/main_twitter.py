import requests
from datetime import datetime, timedelta
import random
import re
import time
import ast
import cloudscraper

scraper = cloudscraper.create_scraper()

def get_random_item(items: list, num: int) -> list:
    if len(items) == num:
        return list(set(items))
    results = []
    cnt = 0
    while len(results) < num:
        item = random.choice(items)
        if item not in results:
            results.append(item)
        cnt += 1
        if cnt > len(items) * 2:
            break
    return results

def utf8_to_ascii(s:str, ws=re.compile('\s+', flags=re.M)) -> str:
    s = s.encode("utf8")
    s = s.decode("ascii", errors="replace")
    s = s.replace(u"\ufffd", " ")
    s = ws.sub(" ", s)
    return s.strip()

def get_user_agent():
    with open(f"twitter_scraper/user_agent.txt",'r') as f:
        user_agent = f.read().split('\n')
    user_agent = get_random_item(user_agent, 1)[0]
    return user_agent

def use_proxy():
    with open(f"twitter_scraper/proxy.txt",'r') as f:
        proxy = f.read()
        f.close()
        proxy = ast.literal_eval(proxy)
    return proxy

def get_header():
    header = {
    "Accept":"application/json, text/plain, */*",
    "Accept-Encoding":"gzip, deflate",
    "Accept-Language":"en-US,en;q=0.9",
    "Origin":"https://www.sotwe.com",
    "Referer":"https://www.sotwe.com/",
    "Sec-Fetch-Dest":"document",
    "Sec-Fetch-Mode":"navigate",
    "Sec-Fetch-Site":"none",
    "User-Agent":f"{get_user_agent()}",
    }
    return header

def getTweetProxy(url: str):
    proxies = requests.get('https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&protocol=http&country=all&anonymity=all&timeout=15000&proxy_format=ipport&format=text').text.split('\r\n')
    for i in proxies:
        try:
            proxy = {
                'http': 'http://'+i,
                'https': 'http://'+i
            }
            now = datetime.now()
            doc = scraper.get(url = url, proxies=proxy,headers=get_header(),  timeout=8).json()
            now = datetime.now() - now
            print(now)
            print("using proxy")
            with open(f"./proxy.txt",'w') as f:
                f.write(f"{proxy}")
                f.close()
            return doc, proxy
        except Exception as e:
            print("fail", i, e)
            pass

def scrape_user_tweet(user:str ):
    try:
        docs = []
        user_detail = []
        url = f'https://api.sotwe.com/v3/user/{user}/'
        proxy = {}
        for i in range(2,5):
            try:
                doc = scraper.get(url=url, headers=get_header()).json()
            except Exception as e:
                try:
                    if not proxy:
                        doc = scraper.get(url=url, proxies=use_proxy(), headers=get_header(), timeout=10).json()
                        print(f"done with: {use_proxy()}")
                    elif proxy:
                        doc = scraper.get(url=url, proxies=proxy, headers=get_header(), timeout=10).json()
                        print(f"done with: {proxy}")
                except Exception as e:
                    doc, proxy = getTweetProxy(url)
                    
            if i == 2:
                user_detail = doc['info']
            after = doc['after']
            url = f'https://api.sotwe.com/v3/user/{user}/?after={after}&page={i}'
            for x in doc['data']:
                docs.append(x)
            # print(len(docs))
        return docs, user_detail
    except Exception as e:
        docs= docs if docs else []
        user_detail= user_detail if user_detail else []
        print("error", e)
        return docs, user_detail

def scrape_keyword_tweet(keyword:str ) -> list:
    docs = []
    url = f'https://api.sotwe.com/v3/search/tweet?q={keyword}'
    for i in range(10):
        try:
            doc = scraper.get(url=url, headers=get_header()).json()
        except Exception as e:
            print(1, e)
            try:
                doc = scraper.get(url=url, proxies=use_proxy(), headers=get_header(), timeout=10).json()
                print(f"done with: {use_proxy()}")
            except Exception as e:
                print(2, e)
                try:
                    doc, proxy = getTweetProxy(url)     
                except Exception as e:
                    print(3, e)
        for data in doc['data']:
            if keyword in data['text']:
                docs.append(data)
        # print(len(docs))
        after = doc['after']
        url = f'https://api.sotwe.com/v3/search/tweet?q={keyword}&after={after}'
    return docs


def serialize_tweet(docs:list, user_detail: list = None) -> list:
    result = []
    i = 0
    if user_detail:
        user = user_detail
    
    for doc in docs:
        if not user_detail:
            user = doc['user']
            print("get target tweet profile: ", user['screenName'])

    #date
        now = datetime.now() - timedelta(hours=24)
        twitter_date = datetime.fromtimestamp((doc['createdAt']/1000))
        # now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= twitter_date:
            if i == 3:
                break
            print("expired")
            print(now, twitter_date)
            i+=1
            continue
    #images
        if doc['mediaEntities']:
            images = []
            for i in range(0, len(doc['mediaEntities'])):
                images.append(doc['mediaEntities'][i]['mediaURL'])
        else:
            images = None
    #inReplyToStatusId
        try:
            inreplytostatusid = doc['inReplyToStatusId']
        except:
            inreplytostatusid = None
    #source
        source = f"https://twitter.com/{user['screenName']}/status/{doc['id']}"
    #mentions
        try:
            mentions = []
            for i in range(0, len(doc['userMentionEntities'])):
                ume = {'name':doc['userMentionEntities'][i]['name'], 'screen_name':doc['userMentionEntities'][i]['screenName']}
                mentions.append(ume)
        except Exception:
            mentions = []
    #tweet
        tweet = utf8_to_ascii(doc["text"])
      
    #serialize        
        twit_top_dict = {
            "avatar": user['profileImageOriginal'],
            "comments_count": int(doc['quoteCount'])+int(doc['replyCount']),
            "content": tweet,
            "created_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "date": twitter_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "followers_count": user['followerCount'],
            "followings_count": user['followingCount'],
            "images": images,
            "in_reply_to_status_id_str": inreplytostatusid,
            "language": "id",
            "likes_count": doc["favoriteCount"],
            "location": user['location'],
            "name": user['name'],
            # "platform": "Twitter",
            "retweets_count": doc["retweetCount"],
            "url": source,
            "user_description": utf8_to_ascii(user["description"]),
            "username": user["screenName"],
            "tweets_count": user['postCount'],
            "post_id": doc["id"],
            "tweet_mentions": mentions,
        }
        result.append(twit_top_dict)

    return result

def scrape_by_acc(accounts: list) -> list:
    for acc in accounts:
        print("\n")
        print("Scraping", acc)
        docs, user_detail = scrape_user_tweet(acc)
        try:
            result = serialize_tweet(docs, user_detail=user_detail)
        except:
            continue
        time.sleep(random.randint(8,13))
        
        print("Total tweet: ", len(result))
    return result

def scrape_by_keyword(keywords: list) -> list:
    for keyword in keywords:
        print("\n")
        print("Scraping for keyword: ", keyword)
        try:
            docs = scrape_keyword_tweet(keyword)
            result = serialize_tweet(docs)
        except Exception as e:
            print(e)
            continue
        time.sleep(10)
    print("Total tweet: ", len(result))
    return result
