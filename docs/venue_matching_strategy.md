The 3-layer matching strategy

Layer 1: Deterministic matches (fast + zero risk)

Exact match after normalization (casefold, whitespace collapse)
Alias table match (venue_aliases.alias_normalized == location_normalized)
Slug match (if you ever store slugs in text)
Known substring matches (e.g., “ringling” contained in the location text)
This catches a surprising amount.

Layer 2: Fuzzy matching with a threshold (safe automation)

When no deterministic match is found, do fuzzy:
Option A (recommended): Python fuzzy matching with rapidfuzz
Very fast
Great accuracy
Works without DB extensions
Workflow:
Normalize location_text (“The Oval at The Bay Sarasota, 1055 Blvd…” → tokens)

Compare against:
venues.name
maybe venues.address
and existing venue_aliases.alias
Take the best score
If score ≥ 90 (or similar), auto-assign
If score is 75–89, create a suggestion for manual review
If < 75, leave unmapped
This keeps you from accidentally mapping “Payne Park” to “Bayfront Park” or similar.

Option B: Postgres fuzzy matching with pg_trgm (great later)
Postgres has a legit trigram similarity extension:
enable: CREATE EXTENSION pg_trgm;
then you can do: WHERE similarity(venue.name, :text) > 0.6 ORDER BY similarity DESC

Pros:
You can do fuzzy matching in pure SQL (nice for admin screens)
Cons:
Requires enabling an extension (fine, but slightly more “DB-admin-y”)

Layer 3: Human-in-the-loop review (best long-term quality)
Even with fuzzy matching, you’ll want a review step for ambiguous cases.
This is where a small table shines:
venue_match_suggestions
occurrence_id
candidate_venue_id
score
status (pending/accepted/rejected)
timestamps
Then you can build a tiny admin page later:
“20 unmapped locations”
click one → see top 5 suggested venues
accept → creates an alias so it auto-maps next time
Normalization is the secret sauce
Fuzzy matching gets way better if you normalize first:
lowercase
strip punctuation
remove “fl”, “sarasota”, “united states”
collapse whitespace
optionally remove ZIP codes
optionally remove street suffix noise (“st”, “street”, “road”, etc.)
You can also keep two normalized forms:
location_norm_namey (venue-ish tokens)
location_norm_addressy (address-ish tokens)
That helps you avoid matching an address string to the wrong venue name.
