import json
import requests
import logging

import falcon
from config import sites

# Frequency of requests for specific tag
tags = {}

def FindFirst(data, begin_str, end_str):
    start = data.find(begin_str)
    if start == -1: return
    start_next = start + len(begin_str)
    end = data.find(end_str, start_next)
    if end is not -1:
        return data[start_next:end]

def FindAll(data, begin_str, end_str):
    start = end = 0
    begin_str_len = len(begin_str)
    while end is not -1:
        start = data.find(begin_str, start)
        if start == -1: return
        start_next = start + len(begin_str)
        end = data.find(end_str, start_next)
        if end is not -1:
            yield data[start_next:end]
            start = end + len(end_str)

def FindData(site, html, begin_str_index, end_str_index):
    return FindFirst(html, sites[site][begin_str_index], sites[site][end_str_index])

def GetPage(url):
    return requests.get(url, headers={'Accept-Encoding':'gzip'}, timeout=None).text

def ParseTwitter(html):
    users = {}
    begin_str = sites['twitter'][2]
    end_str = sites['twitter'][3]

    # Collect usernames
    # Collect users' data
    
    for username in list(set(FindAll(html, begin_str, end_str))):
        profile_html = GetPage(sites['twitter'][0] + '/' + username)
        followers = FindFirst(profile_html,'followers_count&quot;:',',')
        users[username] = followers
    return users

def ParseInstagram(html):
    users = {}
    # Extract JSON
    json_str = FindData('instagram', html, 2, 3)
    # Collect shortnames
    json_data = json.loads(json_str)
    nodes_count = json_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['count']

    for node in json_data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['edges']:
        shortcode = node['node']['shortcode']
        data_html = GetPage(sites['instagram'][0] + '/p/' + shortcode + '/')
        username_html = FindData('instagram', data_html, 4, 5)

        if username_html:
            username_index = username_html.find(sites['instagram'][6])
            if username_index is not -1:
                username_end = username_html.find(sites['instagram'][7], username_index+len(sites['instagram'][6]))
                if username_end is not -1:
                    if username_html[:username_end].endswith(')'):
                        username_end -= 1
                    username = username_html[username_index+len(sites['instagram'][6]):username_end]
                    profile_html = GetPage(sites['instagram'][0] + '/' + username)
                    followers = FindFirst(profile_html,'"edge_followed_by":{"count":','}')
                    users[username] = followers

    # Collect users' data
    return users

class TagstatStorage(object):

    def get_tag(self, tag):
        if tag in tags:
            result = tags[tag]
        else:
            result = 0
        return result

    def set_tag(self, tag):
        if tag in tags:
            tags[tag] += 1
        else:
            tags[tag] = 1
        return True

class TagstatResource(object):

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('tagstat.' + __name__)

    def on_get(self, req, resp, tag):
        resp_json_txt = '{'

        # Get count of requests for this tag
        result = self.db.get_tag(tag)

        resp_json_txt += '"tag_requests":' + str(result) + ','

        for url in sites:
            html = GetPage(sites[url][0] + sites[url][1] + tag + '/')
            resp_json_txt += '"' + url + '":{'

            if url == 'twitter':
                users = ParseTwitter(html)
            elif url == 'instagram':
                users = ParseInstagram(html)

            user_max = max(users, key=users.get)
            self.logger.info('User: ' + user_max + ', Followers:' + str(users[user_max]))
            resp_json_txt += '"user":"' + user_max + '","followers":' + str(users[user_max]) + '},'
            users.clear()

        resp_json_txt = resp_json_txt[:-1] + '}'
        print(resp_json_txt)

        # Store count of requests for this tag
        result = self.db.set_tag(tag)

        resp.status = falcon.HTTP_200
        resp.body = resp_json_txt

app = falcon.API()

db = TagstatStorage()
tagstats = TagstatResource(db)

app.add_route('/tag/{tag}', tagstats)