# Google Play store collection QA

- Snapshot: 2026-09-21T13:02:19.616Z; locale hl=en&gl=IN; runtime date 2026-09-21.
- Records: 70; core 32/32; supplementary 38.
- Status all: {"ok":68,"partial":2}; core: {"ok":32}.
- Missing core IDs: none; duplicate IDs: none.
- Automated evidence checks: PASS. All populated numeric/date values cross-checked against readable app-header/description or preserved JSON-LD; raw HTML SHA-256 verified.
- Unknown flags (not false): {"containsAds":3,"inAppPurchases":7,"offlineClaim":7}.
- Header versus Ratings-and-reviews section count differences: 68. Per-product notes preserve both.

## Metric boundaries
- Public unauthenticated Google Play HTML, observed at runtime date; locale hl=en&gl=IN. No installation/device tests, private APIs, paid data, or DAU estimates.
- Downloads badge = global cumulative Google Play download bucket for this package; NOT current installed base, unique users, India installs, recent downloads or DAU. Lower bound only, not an exact total.
- rating is the visibly rounded app-header star rating for this locale. JSON-LD raw ratingValue is retained in evidence but is not substituted for the displayed star value.
- ratingCount is exact JSON-LD aggregateRating.ratingCount, explicitly a structured ratings count. ratingCountDisplay preserves header text including its original reviews/ratings label; it is rounded and must not be interpreted as the exact structured count or exact number of written reviews.
- Header reviews and lower Ratings-and-reviews section can differ; preserve header and note differences. These locale/device display values need not be comparable to previous snapshots.
- Contains ads / IAP / Offline = store labels or affirmative developer description only, not real-device behavior, ad frequency, business-model mix or offline ad availability. A missing label remains null, never false.
- status ok means identity + numeric/date fields parsed successfully; unknown optional flags remain null. partial means some primary fields absent; unavailable means no public SoftwareApplication identity extracted. Unavailable in IN is not proof of global delisting.
- core=true exactly identifies the 32 CSV references, not 32 approved investments. Supplementary references core=false; explicit cash/reward risk examples, newly observed gambling-content descriptors, and full-football topic-only examples are excluded and recorded in store-inputs.json.

## 32-core coverage and field-missing checklist
Structured count column is JSON-LD ratingCount, NOT exact written reviews. Header text is original rounded label. Optional unknown flags do not cause status partial; absent primary values do.

|#|Package|Current public title|Status|Global cumulative Downloads bucket|Displayed stars|Structured ratingCount|Original header count|Updated on|Missing primary|Unknown flags|
|---|---|---|---|---|---|---|---|---|---|---|---|
|1|com.kooapps.pianotiles2gp|Piano Tiles 2™ - Piano Game|ok|10M+|4.1|74754|74.8K reviews|Sep 9, 2026|none|none|
|2|com.youmusic.magictiles|Magic Tiles 3™ - Piano Game|ok|500M+|4.6|3531580|3.53M reviews|Sep 1, 2026|none|none|
|3|piano.game.music.beat.tiles|Piano Beat: Music Game|ok|10M+|4.3|43903|43.9K reviews|Sep 10, 2026|none|none|
|4|com.amanotes.beathopper|Tiles Hop EDM Rush Music Game|ok|500M+|4.3|3364099|3.36M reviews|Sep 21, 2026|none|none|
|5|solitaire.patience.card.games.klondike.free|Solitaire - Classic Card Games|ok|50M+|4.8|706043|706K reviews|Sep 16, 2026|none|none|
|6|com.easybrain.spider.solitaire|Spider Solitaire|ok|10M+|4.3|156689|157K reviews|Aug 11, 2026|none|none|
|7|com.tonielro.naijawhotfree|Naija Whot|ok|5M+|4.5|23421|23.4K reviews|Jul 30, 2026|none|none|
|8|io.teslatech.callbreak|Callbreak.com - Tash Game|ok|100M+|4.3|546346|546K reviews|Sep 17, 2026|none|none|
|9|com.zlevelapps.cardgame29|Card Game 29|ok|10M+|4.2|106723|107K reviews|Sep 16, 2026|none|none|
|10|com.abyadtherock.egybasraarab|Egyptian Basra Arabic|ok|1M+|4|8928|8.93K reviews|Aug 26, 2025|none|inAppPurchases|
|11|com.ludo.king|Ludo King®|ok|1B+|4|10319393|10.3M reviews|Sep 8, 2026|none|none|
|12|com.tonielrosoft.classicludofree|Naija Ludo|ok|10M+|3.5|47053|47.1K reviews|Sep 3, 2026|none|none|
|13|com.LoopGames.Domino|Dominoes|ok|100M+|4.5|2127239|2.13M reviews|Sep 7, 2026|none|none|
|14|com.snake.io.slither.worms|Snake Lite® - Worm Snake Game|ok|100M+|3.9|487119|487K reviews|Sep 10, 2026|none|none|
|15|com.wildspike.wormszone|Worms Zone .io - Hungry Snake|ok|500M+|4.3|3239459|3.24M reviews|Sep 9, 2026|none|none|
|16|com.amelosinteractive.snake|Snake.io - Fun Snake .io Games|ok|100M+|4.1|1268968|1.27M reviews|Sep 19, 2026|none|none|
|17|com.kiloo.subwaysurf|Subway Surfers|ok|1B+|4.4|41548874|41.5M reviews|Sep 17, 2026|none|none|
|18|com.imangi.templerun2|Temple Run 2|ok|1B+|4|9834519|9.83M reviews|Sep 9, 2026|none|none|
|19|com.fingersoft.hillclimb|Hill Climb Racing|ok|1B+|4|10587568|10.6M reviews|Aug 6, 2026|none|none|
|20|com.soccer.score.star|Soccer Superstar|ok|100M+|4.4|3496229|3.5M reviews|Sep 16, 2026|none|none|
|21|com.miniclip.eightballpool|8 Ball Pool|ok|1B+|4.7|31770986|31.8M reviews|Sep 18, 2026|none|none|
|22|com.miniclip.carrom|Carrom Pool: Disc Game|ok|500M+|4.6|7947415|7.95M reviews|Aug 31, 2026|none|none|
|23|com.miniclip.cricketleague|Cricket League|ok|100M+|4.5|3767447|3.77M reviews|Sep 7, 2026|none|offlineClaim|
|24|com.h8games.helixjump|Helix Jump|ok|100M+|4.1|4144730|4.14M reviews|Sep 17, 2026|none|offlineClaim|
|25|com.JindoBlu.TwoPlayerGamesChallenge|2 Player games : the Challenge|ok|100M+|4.5|730557|731K reviews|Sep 9, 2026|none|none|
|26|com.easybrain.arrow.puzzle.game|Arrow Puzzle: Tap Puzzle Games|ok|50M+|4.5|1395640|1.4M reviews|Sep 4, 2026|none|none|
|27|com.oakever.tiletrip|Tile Explorer - Triple Match|ok|100M+|4.5|2269425|2.27M reviews|Sep 16, 2026|none|none|
|28|com.pixel.art.coloring.color.number|Happy Color®: Color by Number|ok|100M+|4.4|3894686|3.89M reviews|Sep 7, 2026|none|none|
|29|com.easybrain.jigsaw.puzzles|Jigsaw Puzzles - Puzzle Games|ok|100M+|4.5|2375237|2.38M reviews|Sep 11, 2026|none|none|
|30|com.master.hotelmaster|My Perfect Hotel|ok|100M+|4.3|1840150|1.84M reviews|Sep 8, 2026|none|none|
|31|com.outfit7.mytalkingtom2|My Talking Tom 2: Pet Game|ok|1B+|4.2|6749102|6.75M reviews|Sep 7, 2026|none|none|
|32|com.JindoBlu.Antistress|Antistress - relaxation toys|ok|100M+|4.2|976022|976K reviews|Sep 10, 2026|none|none|

## Partial / unavailable records
- com.ayoolopon.app: partial, HTTP 200; missing rating, ratingCount, ratingCountDisplay, ratingCountLabel. Locale page unavailability does not establish global delisting.
- com.gaitco.domono: partial, HTTP 200; missing rating, ratingCount, ratingCountDisplay, ratingCountLabel. Locale page unavailability does not establish global delisting.

## Excluded risk or topic-only examples
- com.ludonairapro: Reward/cash-oriented risk example, not a candidate.
- com.ludo.master.hippo: Newly observed 18+ / Prominent Gambling Imagery descriptor in current Play header; excluded from candidate references. Not evidence of real-money gambling. Snapshot retained at research/html-data/store-snapshots/com.ludo.master.hippo.txt.
- com.big.ludocafe: Newly observed 18+ / Simulated Gambling descriptor in current Play header; excluded from candidate references. Not evidence of real-money gambling. Snapshot retained at research/html-data/store-snapshots/com.big.ludocafe.txt.
- com.hfhy.waje.special: Explicit real-money gambling risk example, excluded.
- com.nicademia.whotmoney: Explicit cash withdrawal/reward risk example, excluded.
- com.firsttouchgames.dls7: Full football simulator: topic-demand context only, not the light-game candidate.
- com.football.soccer.league: Full football simulator: topic-demand context only, not the light-game candidate.
- jp.konami.pesam: Full football simulator: topic-demand context only, not the light-game candidate.

## Evidence / reproducibility
- store-products.json: requested normalized data; store-inputs.json: core/source provenance and exclusions.
- store-snapshots/<package>.txt: readable original header + description/tags + JSON-LD + complete text.
- store-snapshots/<package>.html and .meta.json: raw HTML, HTTP status, exact per-request fetch time, SHA-256.
- node research/html-data/store-fetch.mjs: concurrency 3, 1.1-second worker pacing, 45-second timeout, stop new requests on 429, no auto-retries; saved raw snapshots reused.
- node research/html-data/store-qa.mjs: rebuild this coverage/evidence QA without network requests.
- Public store claims only, not gameplay, device, revenue, retention or country-install measurements.
