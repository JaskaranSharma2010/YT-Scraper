from googleapiclient.discovery import build
import pandas as pd
import time
import re

# ==================================================
# CONFIG
# ==================================================

API_KEY = "YOUR_API"

TARGET_CHANNELS = 1000

SEARCH_TERMS = [
    "make money online",
    "online business",
    "AI automation",
    "AI business",
    "passive income",
    "wealth mindset",
    "luxury lifestyle",
    "financial freedom",
    "entrepreneur motivation",
    "startup motivation",
    "internet entrepreneur",
    "high income skills",
    "creator economy",
    "faceless youtube",
    "youtube automation",
    "business documentary",
    "self improvement money",
    "digital freedom",
    "millionaire habits",
    "agency owner",
    "ecommerce business",
    "dropshipping business",
    "online guru",
    "wealth habits",
    "luxury success",
]

# tier 1 indicators
TIER1_KEYWORDS = [
    "usa",
    "united states",
    "canada",
    "uk",
    "united kingdom",
    "australia",
    "london",
    "new york",
    "los angeles",
    "toronto",
    "miami",
    "california",
]

youtube = build(
    "youtube",
    "v3",
    developerKey=API_KEY
)

# ==================================================
# STORAGE
# ==================================================

seen_channels = set()
all_channels = []

# ==================================================
# GURU SCORE
# ==================================================

guru_keywords = [
    "money",
    "wealth",
    "luxury",
    "millionaire",
    "mindset",
    "entrepreneur",
    "freedom",
    "business",
    "income",
    "ai",
    "passive",
    "success",
]

def guru_score(text):

    text = text.lower()

    score = 0

    for word in guru_keywords:
        if word in text:
            score += 1

    return score

# ==================================================
# FACE/FACELESS DETECTION
# ==================================================

def detect_channel_type(description):

    text = description.lower()

    faceless_words = [
        "documentary",
        "ai voice",
        "automation",
        "business stories",
        "explained",
        "voiceover",
    ]

    for word in faceless_words:
        if word in text:
            return "Faceless"

    return "Face"

# ==================================================
# TIER 1 DETECTION
# ==================================================

def likely_tier1(text):

    text = text.lower()

    for word in TIER1_KEYWORDS:
        if word in text:
            return "Likely"

    return "Unknown"

# ==================================================
# CHANNEL DATA
# ==================================================

def get_channel_data(channel_id, keyword):

    try:

        response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        if not response["items"]:
            return None

        item = response["items"][0]

        snippet = item["snippet"]
        stats = item["statistics"]

        title = snippet.get("title", "")
        description = snippet.get("description", "")
        country = snippet.get("country", "")

        combined_text = (
            title + " " +
            description + " " +
            country
        )

        custom_url = snippet.get("customUrl", "")

        if custom_url:
            channel_link = f"https://youtube.com/{custom_url}"
        else:
            channel_link = (
                f"https://youtube.com/channel/{channel_id}"
            )

        # skip tiny channels
        subs = int(stats.get("subscriberCount", 0))

        if subs < 1000:
            return None

        return {
            "Channel Name": title,
            "Channel Link": channel_link,
            "Subscribers": subs,
            "Views": stats.get("viewCount", 0),
            "Videos": stats.get("videoCount", 0),
            "Country": country,
            "Likely Tier1": likely_tier1(combined_text),
            "Type": detect_channel_type(description),
            "Guru Score": guru_score(combined_text),
            "Found From Keyword": keyword,
            "Description": description[:250]
        }

    except Exception as e:
        print("Channel Error:", e)
        return None

# ==================================================
# SEARCH
# ==================================================

for keyword in SEARCH_TERMS:

    print(f"\nSearching keyword: {keyword}")

    next_page_token = None

    for page in range(15):

        if len(all_channels) >= TARGET_CHANNELS:
            break

        try:

            response = youtube.search().list(
                q=keyword,
                part="snippet",
                type="video",
                relevanceLanguage="en",
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            items = response.get("items", [])

            for item in items:

                channel_id = item["snippet"]["channelId"]

                if channel_id in seen_channels:
                    continue

                seen_channels.add(channel_id)

                data = get_channel_data(
                    channel_id,
                    keyword
                )

                if data:

                    all_channels.append(data)

                    print(
                        f"{len(all_channels)} | "
                        f"{data['Channel Name']} | "
                        f"{data['Type']}"
                    )

                if len(all_channels) >= TARGET_CHANNELS:
                    break

            next_page_token = response.get(
                "nextPageToken"
            )

            if not next_page_token:
                break

            time.sleep(1)

        except Exception as e:
            print("Search Error:", e)
            break

# ==================================================
# EXPORT
# ==================================================

df = pd.DataFrame(all_channels)

df = df.sort_values(
    by=[
        "Guru Score",
        "Subscribers"
    ],
    ascending=False
)

df.to_csv(
    "1000_youtube_channels.csv",
    index=False
)

print("\nDONE.")
print(f"Extracted {len(all_channels)} channels.")
