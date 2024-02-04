AUTHOR = 'Kevin D. Reid'
SITENAME = "Kevin's Tech Blog"
SITEURL = ""

PATH = "content"

TIMEZONE = 'America/Vancouver'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Links
LINKS = (
    ("mail@kevindreid.com", "mailto:mail@kevindreid.com"),
    ("LinkedIn", "https://www.linkedin.com/in/kevin-d-reid"),
    ("Github", "https://github.com/kevin-d-reid"),
    # ("You can modify those links in your config file", "#"),
)

DEFAULT_PAGINATION = 5

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True

AUTHOR_URL = 'author/{slug}'
CATEGORY_URL = 'category/{slug}'
TAG_URL = 'tag/{slug}'

THEME = 'theme/octopress'