import re
import csv
import json
import time
import random
import requests

from urllib.parse import quote


START_URLS = [

    "https://nicegram.app/hub/channels?lang=ar"

]


BASE_CHANNELS = (
    "https://nicegram.app/hub/channels?lang=ar&cursor="
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    )
}


MAX_PAGES_PER_RUN = 300

CSV_FILE = "nicegram_dump.csv"

QUEUE_FILE = "queue.json"


users = set()

visited_pages = set()

visited_cursors = set()

queue = []

pages_done = 0

zero_hits = 0


session = requests.Session()

session.headers.update(HEADERS)


def load_existing_users():

    try:

        with open(
            CSV_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            reader = csv.reader(f)

            next(reader, None)

            for row in reader:

                if len(row) >= 1:

                    users.add(row[0])

        print(f"LOADED USERS: {len(users)}")

    except:

        print("NO OLD CSV")


def load_queue():

    global queue

    try:

        with open(
            QUEUE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            queue = json.load(f)

        print(f"LOADED QUEUE: {len(queue)}")

    except:

        print("NEW QUEUE")

        queue = START_URLS.copy()


def save_queue():

    with open(
        QUEUE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(queue, f)


def save_users():

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "username",
            "link"
        ])

        for user in sorted(users):

            writer.writerow([
                user,
                f"https://t.me/{user}"
            ])

    print(f"CSV SAVED: {len(users)} USERS")


def fetch_page(url, retries=5):

    for attempt in range(retries):

        try:

            print("\nSCRAPING:")
            print(url)

            response = session.get(
                url,
                timeout=30
            )

            response.raise_for_status()

            return response.text

        except Exception as e:

            print(f"ERROR: {e}")

            wait = 5 + (attempt * 3)

            print(f"SLEEP: {wait}s")

            time.sleep(wait)

    return None


def extract_users(html):

    global zero_hits

    matches = re.findall(
        r"t\.me\/([a-zA-Z0-9_]+)",
        html
    )

    before = len(users)

    for user in matches:

        users.add(user)

    added = len(users) - before

    print(f"NEW USERS: {added}")

    print(f"TOTAL USERS: {len(users)}")

    if added == 0:

        zero_hits += 1

    else:

        zero_hits = 0


def extract_cursors(html):

    matches = re.findall(
        r'cursor=([^"&]+)',
        html
    )

    result = []

    for c in matches:

        c = c.replace("\\", "").strip()

        if not c:
            continue

        if c in visited_cursors:
            continue

        visited_cursors.add(c)

        result.append(c)

    return result


def build_next_url(cursor):

    return (
        BASE_CHANNELS +
        quote(cursor)
    )


load_existing_users()

load_queue()


while queue:

    if pages_done >= MAX_PAGES_PER_RUN:

        print("\nLIMIT REACHED")

        break


    current = queue.pop(0)

    if current in visited_pages:
        continue

    visited_pages.add(current)

    html = fetch_page(current)

    if not html:
        continue


    extract_users(html)

    cursors = extract_cursors(html)

    print(f"CURSORS: {len(cursors)}")


    for cursor in cursors:

        next_url = build_next_url(cursor)

        if next_url not in visited_pages:

            queue.append(next_url)


    print(f"QUEUE: {len(queue)}")

    pages_done += 1

    print(f"PAGES DONE: {pages_done}")

    print(f"VISITED PAGES: {len(visited_pages)}")

    print(f"ZERO HITS: {zero_hits}")


    if pages_done % 10 == 0:

        save_users()

        save_queue()


    sleep_time = random.uniform(3, 6)

    print(f"SLEEP: {sleep_time:.2f}s")

    time.sleep(sleep_time)


save_users()

save_queue()

print("\nRUN FINISHED")

print(f"TOTAL USERS: {len(users)}")
