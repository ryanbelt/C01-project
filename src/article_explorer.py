"""
This script retrieves monitoring site, foreign sites,
and keywords from Django database and looks into the monitoring
sites to find matching foreign sites or keywords.
newspaper package is the core to extract and retrieve relevant data.
If any keyword (of text) or foreign sites (of links) matched,
the Article will be stored at Django database as articles.models.Article.
Django's native api is used to easily access and modify the entries.
"""

__author__ = "ACME: CSCC01F14 Team 4"
__authors__ = \
    "Yuya Iwabuchi, Jai Sughand, Xiang Wang, Kyle Bridgemohansingh, Ryan Pan"

import sys
import os

# Add Django directories in the Python paths for django shell to work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                             'Frontend')))
# Append local python lib to the front to assure
# local library(mainly Django 1.7.1) to be used
sys.path.insert(0, os.path.join(os.environ['HOME'],
                                '.local/lib/python2.7/site-packages'))
# newspaper, for populating articles of each site
# and parsing most of the data.
import newspaper
# Used for newspaper's keep_article_html as it was causing error without it
import lxml.html.clean
# Regex, for parsing keywords and sources
import re
# Mainly used to make the explorer sleep
import time
import timeit
# For getting today's date with respect to the TZ specified in Django Settings
from django.utils import timezone
# For extracting 'pub_date's string into Datetime object
from dateutil import parser
# To connect and use the Django Database
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'Frontend.settings'
# For Models connecting with the Django Database
from articles.models import*
from articles.models import Keyword as A_keyword
from explorer.models import*
from explorer.models import Keyword as E_keyword
# To load configurations
import yaml
# To store the article as warc files
import warc_creator


def configuration():
    """ (None) -> dict
    Returns a dictionary containing the micro settings from the
    config.yaml file located in the directory containing this file
    """
    config_yaml = open("../config.yaml", 'r')
    conf = yaml.load(config_yaml)
    config_yaml.close()
    return conf


def populate_sites(sites):
    """ (list of str) -> list of [str, newspaper.source.Source]
    Parses through the sites using newspaper library and
    returns list of sites with available articles populated

    Keyword arguments:
    sites         -- List of [name, url] of each site
    """
    new_sites = []
    for s in range(len(sites)):
        # Check for any new command on communication stream
        check_command()
        # Duplicate the name of the sites
        new_sites.append([sites[s][0]])
        # Use the url and populate the site with articles
        new_sites[s].append((newspaper.build(sites[s][1],
                                             memoize_articles=False,
                                             keep_article_html=True,
                                             fetch_images=False,
                                             language='en',
                                             number_threads=1)))
        # Append site url
        new_sites[s].append(sites[s][1])
    return new_sites


def parse_articles(populated_sites, db_keywords, foreign_sites):
    """ (list of [str, newspaper.source.Source, str],
         list of str, list of str, str) -> None
    Downloads each article in the site, extracts, compares
    with Foreign Sites and Keywords provided.
    Then the article which had a match will be stored into the Django database

    Keyword arguments:
    populated_sites     -- List of [name, 'built_article'] of each site
    db_keywords         -- List of keywords
    foreign_sites       -- List of foreign sites
    """
    added, updated, failed, no_match = 0, 0, 0, 0

    # for each article in each sites, download and parse important data
    for site in populated_sites:
        # print "\n%s" % site[0]
        article_count = site[1].size()
        processed = 0
        for k in range(len(site[1].articles)):
            art = site[1].articles[k]
            # Stop any print statements, even newspaper's warning messages
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")

            # Check for any new command on communication stream
            check_command()

            url = art.url
            if 'http://www.' in url:
                url = url[:7] + url[11:]
            elif 'https://www.' in url:
                url = url[:8] + url[12:]

            # Try to download and extract the useful data
            try:
                art.download()
                art.parse()
                title = art.title
            except:
                title = ""
            # If downloading/parsing the page fails,
            # stop here and move on to next article
            if not ((title == "") or (title == "Page not found")):
                # Regex the keyword from the article's text
                keywords = get_keywords(art, db_keywords)
                # Regex the links within article's html
                sources = get_sources(art.article_html, foreign_sites)
                # Store parsed author
                authors = art.authors
                # Try to parse the published date
                pub_date = get_pub_date(art)

                # If neither of keyword nor sources matched,
                # then stop here and move on to next article
                if not (keywords == [] and sources == []):

                    # Check if the entry already exists
                    article_list = Article.objects.filter(url=url)
                    if not article_list:
                        # If the article is new to the database,
                        # add it to the database
                        article = Article(title=title, url=url,
                                          url_origin=site[2],
                                          date_added=timezone.localtime(
                                              timezone.now()),
                                          date_published=pub_date)
                        article.save()

                        article = Article.objects.get(url=url)

                        for key in keywords:
                            article.keyword_set.create(keyword=key)

                        for author in authors:
                            article.author_set.create(author=author)

                        for source in sources:
                            article.source_set.create(url=source[0],
                                                      url_origin=source[1])

                        added += 1

                    else:
                        # If the article already exists,
                        # update all fields except date_added
                        article = article_list[0]
                        article.title = title
                        article.url = url
                        article.url_origin = site[2]
                        # Do not update the added date
                        # article.date_added = today
                        article.date_published = pub_date
                        article.save()

                        for key in keywords:
                            if not A_keyword.objects.filter(keyword=key):
                                article.keyword_set.create(keyword=key)

                        for author in authors:
                            if not Author.objects.filter(author=author):
                                article.author_set.create(author=author)

                        for source in sources:
                            if not Source.objects.filter(url=source[0]):
                                src = article.source_set.create(url=source[0])
                                src.url_origin = source[1]

                    warc_creator.create_article_warc(url)

            processed += 1

            # Let the output print back to normal for minimal ui
            sys.stdout = sys.__stdout__
            # Print out minimal information
            sys.stdout.write(
                "%s (Article|%s) %i/%i          \r" %
                (str(timezone.localtime(timezone.now()))[:-13],
                 site[0], processed, article_count))
            sys.stdout.flush()
            # Null the article data to free the memory
            site[1].articles[k] = None
        print(
            "%s (Article|%s) %i/%i          " %
            (str(timezone.localtime(timezone.now()))[:-13], site[0],
             processed, article_count))


def get_sources(html, sites):
    """ (str, list of str) -> list of [str, str]
    Searches and returns links redirected to sites within the html
    links will be storing the whole url and the domain name used for searching.
    Returns empty list if none found

    Keyword arguments:
    html                -- string of html
    sites               -- list of site urls to look for
    """
    matched_urls = []

    # Used to format the url
    regex = "([a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?\\.)+[a-zA-Z]{2,6}"

    # for each site, check if it exists within the html given
    for site in sites:
        for url in re.findall(
                "href=[\"\'][^\"\']*?.*?[^\"\']*?[\"\']", html, re.IGNORECASE):
            # Format the site to use only the domain name for searching
            formatted_site = \
                re.search(regex, site, re.IGNORECASE).group(0)
            if formatted_site[:3] == 'www':
                formatted_site = formatted_site[3:]
            if formatted_site in url:
                # If it matches even once, append the site to the list
                matched_urls.append([url[6:-1], site])
    # Return the list
    return matched_urls


def get_pub_date(article):
    """ (newspaper.article.Article) -> str
    Searches and returns date of which the article was published
    Returns None otherwise

    Keyword arguments:
    article         -- 'Newspaper.Article' object of article
    """
    dates = []

    # For each metadata stored by newspaper's parsing ability,
    # check if any of the key contains 'date'
    for key, value in article.meta_data.iteritems():
        if re.search("date", key, re.IGNORECASE):
            # If the key contains 'date', try to parse the value as date
            try:
                dt = parser.parse(str(value))
                # If parsing succeeded, then append it to the list
                dates.append(dt)
            except:
                pass
    # If one of more dates were found,
    # return the oldest date as new ones can be updated dates
    # instead of published date
    if dates:
        date = sorted(dates, key=lambda x: str(x)[0])[0]
        if timezone.is_naive(date):
            return \
                timezone.make_aware(date,
                                    timezone=timezone.get_default_timezone())
        else:
            return timezone.localtime(date)
    return None


def get_keywords(article, keywords):
    """ (newspaper.article.Article, list of str) -> list of str
    Searches and returns keywords which the article's title or text contains
    Returns empty list otherwise

    Keyword arguments:
    article         -- 'Newspaper.Article' object of article
    keywords        -- List of keywords
    """
    matched_keywords = []

    # For each keyword, check if article's text contains it
    for key in keywords:
        if re.search(key, article.title + article.text, re.IGNORECASE):
            # If the article's text contains the key, append it to the list
            matched_keywords.append(key)
    # Return the list
    return matched_keywords


def explore():
    """ () -> None
    Connects to keyword and site tables in database,
    crawls within monitoring sites, then pushes articles which matches the
    keywords or foreign sites to the article database
    """

    # Retrieve and store monitoring site information
    monitoring_sites = []
    msites = Msite.objects.all()
    for site in msites:
        # monitoring_sites is now in form [['Name', 'URL'], ...]
        monitoring_sites.append([site.name, site.url])

    # Retrieve and store foreign site information
    foreign_sites = []
    fsites = Fsite.objects.all()
    for site in fsites:
        # foreign_sites is now in form ['URL', ...]
        foreign_sites.append(site.url)

    # Retrieve all stored keywords
    keyword_list = []
    keywords = E_keyword.objects.all()
    for key in keywords:
        keyword_list.append(str(key.keyword))

    # Populate the monitoring sites with articles
    populated_sites = populate_sites(monitoring_sites)

    # Parse the articles in all sites
    parse_articles(populated_sites, keyword_list, foreign_sites)


def comm_write(text):
    """ (Str) -> None
    Writes a command to the comm_file of article.
    The file is used to communicate with the running explorer process,
    to change the status safely.

    Keyword arguments:
    text         -- String of command
    """
    # Load the relevant configs
    conf = configuration()['communication']

    # Wait for retry_count * retry_delta seconds
    for k in range(conf['retry_count']):
        try:
            comm = open('article' + conf['comm_file'], 'w')
            comm.write(text)
            comm.close()
            return None
        except:
            time.sleep(conf['retry_delta'])


def comm_read():
    """ (None) -> Str
    Reads the current status or command listed on the comm_file with the
    article, then returns the output.
    """
    # Load the relevant configs
    conf = configuration()['communication']

    # Wait for retry_count * retry_delta seconds
    for k in range(conf['retry_count']):
        try:
            comm = open('article' + conf['comm_file'], 'r')
            msg = comm.read()
            comm.close()
            return msg
        except:
            time.sleep(conf['retry_delta'])


def comm_init():
    """ (None) -> None
    Initialize The communication file
    """
    # Set the current status as Running
    comm_write('RR %s' % os.getpid())


def check_command():
    """ (None) -> None
    Check the communication file for any commands given.
    Execute according to the commands.
    """
    # Load the relevant configs
    conf = configuration()['communication']
    msg = comm_read()

    # Let the output print back to normal for printing status
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    if msg[0] == 'W':
        command = msg[1]
        if command == 'S':
            print('Stopping Explorer...')
            comm_write('SS %s' % os.getpid())
            sys.exit(0)
        elif command == 'P':
            print('Pausing ...')
            comm_write('PP %s' % os.getpid())
            while comm_read()[1] == 'P':
                print('Waiting %i seconds ...' % conf['sleep_time'])
                time.sleep(conf['sleep_time'])
                check_command()
        elif command == 'R':
            print('Resuming ...')
            comm_write('RR %s' % os.getpid())


if __name__ == '__main__':

    # Load the relevant configs
    config = configuration()['article']
    # Connects to Site Database
    django.setup()

    # Initialize Communication Stream
    comm_init()

    # Check for any new command on communication stream
    check_command()

    start = timeit.default_timer()

    # The main function, to explore the articles
    explore()

    end = timeit.default_timer()
    delta_time = end - start
    sleep_time = max(config['min_iteration_time']-delta_time, 0)
    for i in range(int(sleep_time//5)):
        time.sleep(5)
        check_command()

    check_command()

    # Re run the program to avoid thread to increase
    os.chmod('article_explorer_run.sh', 0700)
    os.execl('article_explorer_run.sh', '')
