import requests
import streamlit as st
import pandas as pd
from collections import Counter
import time

APIURL_FOLLOWERS = "https://api.yodayo.com/v1/users/{user_id}/followers?include_nsfw=true"
APIURL_USER_PROFILE = "https://api.yodayo.com/v1/users/{user_uuid}"
secrets = st.secrets["secrets"]

access_token = secrets["access_token"]
session_uuid = secrets["session_uuid"]

# Adjust this value to control the delay between API requests (in seconds)
REQUEST_DELAY = 1.5

def get_followers(session, user_id: str, limit: int = 500) -> list:
    offset = 0
    followers = []

    while True:
        try:
            params = {"limit": limit, "offset": offset}
            response = session.get(APIURL_FOLLOWERS.format(user_id=user_id), params=params)
            response.raise_for_status()

            data = response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to API: {e}")
            break

        if not data.get("users"):
            break

        for follower in data.get("users", []):
            yield follower["user"]["uuid"]

        if len(data.get("users", [])) < limit:
            break

        offset += limit
        time.sleep(REQUEST_DELAY)  # Delay after each API request

def get_user_profile(session, user_uuid: str) -> dict:
    try:
        response = session.get(APIURL_USER_PROFILE.format(user_uuid=user_uuid))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return {}

st.title("Yodayo Shared Followers")

user_id = st.text_input("Enter User ID")

if user_id:
    session = requests.Session()

    jar = requests.cookies.RequestsCookieJar()
    jar.set("access_token", access_token)
    jar.set("session_uuid", session_uuid)
    session.cookies = jar

    followers = list(get_followers(session, user_id))
    followers_info = {follower_uuid: get_user_profile(session, follower_uuid) for follower_uuid in followers}

    with st.spinner("Calculating shared followers..."):
        follower_ids = set(followers_info.keys())
        shared_followers = Counter()

        for follower_id in follower_ids:
            shared_with = follower_ids & set(get_followers(session, follower_id))
            shared_followers[follower_id] = len(shared_with)
            time.sleep(REQUEST_DELAY)  # Delay after each API request

    st.write(f"Number of followers for {user_id}: {len(followers_info)}")

    for follower_id, shared_count in shared_followers.most_common():
        follower_name = followers_info[follower_id].get("profile", {}).get("name", follower_id)
        shared_percentage = (shared_count / len(followers_info)) * 100
        st.write(f"[{follower_name}](https://yodayo.com/1/users/{follower_id}/) - Shared Followers: {shared_count} ({shared_percentage:.2f}%)")
