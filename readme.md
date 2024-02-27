# Twenty Four Lemons Data Fetch

A small python script to fetch 24 Hour of Lemons Race details.  This was created to assist with building out a website to display the races in a map view, with the intention of finding events near you.  The original information can be found on the 24 Hours of Lemons schedule page, https://24hoursoflemons.com/schedule/#all

## Notes

- The program requires a [Google Places (New) API key](https://developers.google.com/maps/documentation/places/web-service/text-search) in order to fetch the geolocation data for various events.
  - Set the value for `GOOGLE_API_KEY` as an [environment variable](https://docs.python.org/3/using/cmdline.html#environment-variables)
- The program generates a json file of the various races and outputs data in to the following format: 
  - ```
      {
        "url": "https://www.google.com",
        "name": "Race Name",
        "dateInfo": "Jan 1 - Jan 3, 2024",
        "eventType": "race",
        "eventCourse": "RaceCourse, City ST",
        "location":
        {
            "coordinates":
            {
                "latitude": 0.0,
                "longitude": -1.1
            },
            "address": "123 Way St City, ST 00000, USA",
            "name": "LocationName
        }
    }
  	```
