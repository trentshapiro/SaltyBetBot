import os
import json
import requests
import asyncpraw
import random



async def random_sub(reddit):
    multi = await reddit.multireddit("user_name", "multireddit_name", fetch = True)
    subs = multi.subreddits
    return random.choice(subs)


async def random_post(reddit):
    this_sub = await random_sub(reddit)

    posts = []
    async for i in this_sub.hot(limit=20):
        if (i.selftext == ''):
            posts = posts + [i]

    if posts is None:
        this_sub = await random_sub(reddit)

        posts = []
        async for i in this_sub.hot(limit=20):
            if (i.selftext == ''):
                posts = posts + [i]

    this_post = random.choice(posts)
    post_title = this_post.title
    post_sub = this_sub
    post_url = this_post.url

    return f'From r/{post_sub}: {post_url}\n"{post_title}"'


async def retrieve_random_post():
    # read creds
    with open(os.getcwd()+'\\credentials\\config.json') as f:
        creds = json.load(f)

    user_agent = 'user agent name'

    with asyncpraw.Reddit(
        client_id = creds['reddit_id'],
        client_secret = creds['reddit_secret'],
        user_agent=user_agent
    ) as reddit:

        return_post = await random_post(reddit)

    

    return return_post
