from typing import Any, Optional, List
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import util
from requests import Session
from pydantic import BaseModel
import json
import os
from json import JSONEncoder


class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class GeoCoordinates(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]


class Location(BaseModel):
    coordinates: Optional[GeoCoordinates]
    address: Optional[str]
    name: Optional[str]


class Event(BaseModel):
    url: str
    name: str
    dateInfo: str
    eventType: str
    eventCourse: str
    location: Optional[Location] = None


DOMAIN = 'https://24hoursoflemons.com'
URL = f'{DOMAIN}/schedule/#race'
PLACES_NEW_API_URL = 'https://places.googleapis.com/v1/places:searchText'
GOOGLE_API_KEY = ''


def get_http_session(
        retries=1,
        backoff_factor=20.0,
        status_forcelist=(500, 502, 504),
        session=None,
        proxy=None,
        user_agent=None,
) -> Session:
    """
    Build request retry policy. Wait by default to 5+ minutes in 5 retries unless these settings overriden by client.
    """
    session = session or Session()
    retry = util.Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    if user_agent:
        session.headers.update({'User-Agent': user_agent})
    if proxy:
        session.proxies.update({'https': proxy})
    return session


def load_env():
    global GOOGLE_API_KEY
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key is None:
        raise Exception('GOOGLE_API_KEY environment variable not found')
    else:
        GOOGLE_API_KEY = api_key


def get_twenty_four_hour_event():
    load_env()
    session = get_http_session()
    response = session.get(URL)
    if response.status_code != 200:
        return None
    event_entries = get_events_entries(response.text)
    events = process_event_entries(event_entries)
    save_events_to_json(events)


def get_events_entries(html: str):
    soup = BeautifulSoup(html, features='html.parser')
    events = soup.select('div.container.mb-20.d-none.d-md-flex')
    return events


def process_event_entries(events: list) -> List[Event]:
    entries_data = []
    for event in events:
        row = event.select('.row')
        cols = row[0].select('div.col-sm')
        event_course = cols[0].text.strip()
        url_path = cols[0].find('a', href=True).attrs['href']
        url = f'{DOMAIN}{url_path}'
        event_type = get_event_type(url_path)
        # rally events do not have a defined location so, just ignore them
        if event_type == 'rally':
            continue
        event_date = get_event_date(cols[1].text.strip())
        name = cols[2].text.strip()
        # don't include duplicates
        if any(e.name == name for e in entries_data):
            continue
        _event = Event(url=url,
                       name=name,
                       dateInfo=event_date,
                       eventType=event_type,
                       eventCourse=event_course)
        _event = update_event_with_location_data(_event)
        entries_data.append(_event)
    return entries_data


def update_event_with_location_data(event: Event) -> Event | None:
    response_json = None
    with get_http_session() as session:
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': GOOGLE_API_KEY,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location'
        }
        response = session.post(PLACES_NEW_API_URL,
                                headers=headers,
                                data=json.dumps({'textQuery': event.eventCourse}))
        if response.status_code == 200:
            response_json = response.json()
    if 'places' in response_json:
        place = response_json['places'][0]
        address = place['formattedAddress']
        latitude = place['location']['latitude']
        longitude = place['location']['longitude']
        name = place['displayName']['text']
        coordinates = GeoCoordinates(latitude=latitude, longitude=longitude)
        event.location = Location(coordinates=coordinates,
                                  address=address,
                                  name=name)
        return event
    return None


def get_event_type(url: str) -> str:
    race = 'race'
    rally = 'rally'
    return race if race in url else rally if rally in url else ''


def get_event_date(text: Any):
    if 'Entry' in text:
        return text[:text.index('Entry')]
    return text


def save_events_to_json(events: List[Event]):
    with open('events.json', 'wt') as f:
        json_data = json.dumps(events, cls=MyEncoder)
        f.write(json_data)


get_twenty_four_hour_event()
