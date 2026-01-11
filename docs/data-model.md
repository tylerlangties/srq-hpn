##Event
id
title
description
venue_id
slug
is_free
price_text        (string, not enum — flexibility matters)
categories table
event_categories join table
source
source_id
external_id
last_seen_at
status            (scheduled | canceled)

##Venue
id
name
address
area
website
slug
timezone          (default: America/New_York)

##EventOccurence
id
event_id
start_datetime_utc
end_datetime_utc (nullable)
