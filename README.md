### NEWS

How to use:
```python
from news_scraper.main_news import scrap, serialize
scrap("./news_scraper/")
data = serialize("./news_scraper/")
```

### Twitter

How to use:
```python
from twitter_scraper.main_twitter import scrape_by_keyword, scrape_by_acc
data = scrape_by_keyword(['elonmusk'])
data = scrape_by_acc(['elonmusk'])
```

### Youtube

How to use
```python
from youtube_scraper.main_yt import scrape
data = scrape(['jokowi'])
```