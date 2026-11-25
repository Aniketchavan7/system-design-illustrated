# Source-Check Plan: Part 5 to the End

This plan covers the case studies (`REAL_WORLD_EXAMPLES.md`) that haven't been source-checked yet. Progress is tracked in [issue #9](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

## Where things stand (November 2026)

| Part | Modules | Status |
| :--- | :--- | :--- |
| 1 · Networking & Traffic | 01–05 | ✅ Done (#11) |
| 2 · Storing Data | 06–09, 29, 30 | ✅ Done (#12) |
| 3 · Caching & Edge | 10–12 | ✅ Done (#14) |
| 4 · Distributed-Systems Thinking | 13–16, 31 | 🔄 In review (#15) |
| 5 · Async Processing & Microservices | 17–20, 33 | ⬜ Next |
| 0 · Foundations | 26–28 | ⬜ |
| 6 · Full System Designs | 21–25, 32, 34–45 | ⬜ (split into three PRs) |

That leaves **26 modules**. Modules 32, 40 and 44 already cite sources, so they need checking against those sources rather than a rewrite.

## Method

These are the rules Parts 1–4 followed. Keep them.

1. **Primary sources only.** Use the company's own engineering post, paper, documentation or repository. Secondary write-ups are leads, not sources.
2. **Keep only what the source says.** Quote the key phrases. If a number or design detail isn't in a source you've read, remove it.
3. **Read the source yourself.** For PDFs, extract the text and search it. A summary of a page is not the page.
4. **Respect sites that block automated reading.** The Netflix Tech Blog refuses automated fetches. Don't work around that. Either read the post in a browser and check the claim by hand, or use Netflix's GitHub repos or its official sites (for example openconnect.netflix.com), or replace the section.
5. **Say what changed.** Each rewritten file ends its deep dives with a short "ℹ️ An earlier version of this page…" note listing what was removed and why.
6. **Mark the file.** Replace the "⚠️ Not yet source-checked" banner with "✅ Source-checked". Name the source at the top of every deep dive.

## Mistakes that kept recurring in Parts 1–4

Expect more of the same in the remaining modules:

- **Misattribution.** Envoy was credited to Google (it was built at Lyft), and Caffeine/W-TinyLFU to Google (an independent project).
- **Invented scale numbers.** For example "100M+ concurrent WebSockets" (Discord's post says about 5 million), "99.8% hit rate" (not in the TAO paper), and "15% of internet traffic" (not on Netflix's Open Connect site).
- **Wrong mechanism names.** Spanner was called "SSI" (it uses two-phase locking), and Facebook's invalidation pipeline "Wormhole" (it's mcsqueal).
- **Mixed-up parameters.** Chubby's 12 s is the client session lease extension, not the master lease.
- **Stale figures.** Cloudflare's network size changes. State the date you read it.

## Checklist for each PR

```bash
python course/build.py                 # regenerate site chapters
python build_rich_flashcards.py         # regenerate flashcards
python -m pytest -q                     # all tests
python course/build.py --check
python build_rich_flashcards.py --check
cmp cards-data.js docs/cards-data.js    # root and docs/ must match
```

- Update the module's callout line in its `README.md` and its row in the main README's case-study table.
- Base every PR on `main`. Don't stack PRs: when a stacked PR's base branch is deleted on merge, GitHub closes the PR instead of retargeting it.
- Tick the module on issue #9 when the PR merges.

## Module-by-module

"Candidate sources" are starting points that haven't been checked yet. Confirm each one says what you need before citing it.

### Part 5 · Async Processing & Microservices (one PR)

| # | Topic | What to check | Candidate sources |
| :-: | :--- | :--- | :--- |
| [17](./17-message-queues/REAL_WORLD_EXAMPLES.md) | Message queues & event streaming | Netflix Keystone "1.5 trillion events/day"; Google Cloud Pub/Sub routing claims. | Kreps et al., *Kafka: a Distributed Messaging System for Log Processing* (NetDB 2011); Apache Kafka docs (design section); Google Cloud Pub/Sub overview docs. |
| [18](./18-event-sourcing-and-cqrs/REAL_WORLD_EXAMPLES.md) | Event sourcing & CQRS | Uber "trip lifecycle engine", Netflix studio pipeline, and "Google Docs uses event sourcing" all look unsourced. Google Docs is usually described as operational transformation, not event sourcing. | Microsoft Azure Architecture Center *Event Sourcing* and *CQRS* pattern pages; Martin Fowler's *Event Sourcing* article; Google Drive blog post on the 2010 Docs editor (for the OT claim, if kept). |
| [19](./19-distributed-transactions/REAL_WORLD_EXAMPLES.md) | Distributed transactions | Percolator details; "Uber & Netflix use sagas (Cadence/Temporal)". | Peng & Dabek, *Large-scale Incremental Processing Using Distributed Transactions and Notifications* (Percolator, OSDI 2010); Garcia-Molina & Salem, *Sagas* (SIGMOD 1987); Cadence and Temporal docs; Netflix Conductor README (conductor-oss). |
| [20](./20-fault-tolerance-and-resilience/REAL_WORLD_EXAMPLES.md) | Fault tolerance & resilience | Netflix chaos-engineering specifics; Google "overload shedding & deadline propagation". | Google SRE book chapters *Addressing Cascading Failures* and *Handling Overload* (the latter is already verified in module 05); Netflix Chaos Monkey GitHub README; principlesofchaos.org; gRPC docs on deadlines. |
| [33](./33-microservices-and-service-mesh/REAL_WORLD_EXAMPLES.md) | Microservices & service mesh | **Title says "Google: The Birth of Envoy". Envoy was built at Lyft** (CNCF announcement, verified for module 04). Check every gRPC/Istio origin claim. | CNCF *CNCF hosts Envoy* (2017, already verified); grpc.io *About*; istio.io history/about page; Netflix OSS GitHub READMEs (Eureka; Hystrix, which says it is in maintenance mode). |

### Part 0 · Foundations (one PR)

| # | Topic | What to check | Candidate sources |
| :-: | :--- | :--- | :--- |
| [26](./26-scaling-from-one-to-millions/REAL_WORLD_EXAMPLES.md) | Scaling from one to millions | "Google evolved from BackRub" narrative; Netflix "15% of global internet traffic" (already removed from module 12 as unsourced). | Brin & Page, *The Anatomy of a Large-Scale Hypertextual Web Search Engine* (1998); Barroso, Dean & Hölzle, *Web Search for a Planet* (IEEE Micro 2003); Netflix newsroom post on completing its cloud migration (2016). |
| [27](./27-back-of-the-envelope-estimation/REAL_WORLD_EXAMPLES.md) | Back-of-the-envelope estimation | "Jeff Dean's numbers" (check the exact table and its date); Netflix "260M subscribers" CDN sizing. | Jeff Dean's LADIS 2009 keynote slides (*Numbers Everyone Should Know*); Netflix shareholder letters for subscriber counts (state the quarter); Open Connect appliance specs (already verified for module 12). |
| [28](./28-distributed-unique-id-generator/REAL_WORLD_EXAMPLES.md) | Distributed unique ID generator | **"Google generates globally ordered IDs with TrueTime & Spanner" looks wrong**: Spanner's docs warn against monotonically increasing keys. Netflix request IDs look unsourced. | Twitter's Snowflake README (twitter-archive/snowflake) and 2010 announcement; Discord developer docs *Snowflakes*; Spanner schema-design docs (hotspots from sequential keys). |

### Part 6a · Full system designs (21–25) (one PR)

| # | Topic | What to check | Candidate sources |
| :-: | :--- | :--- | :--- |
| [21](./21-system-design-url-shortener/REAL_WORLD_EXAMPLES.md) | URL shortener | Bitly "10 billion+ clicks/month"; "Netflix uses URL shortening for TV activation" looks unsourced. | RFC 9110 (301 vs 302 semantics); X/Twitter help page on its t.co link service; Bitly's own published figures (with a date) or drop the number. |
| [22](./22-system-design-in-memory-cache/REAL_WORLD_EXAMPLES.md) | Distributed in-memory cache | Twemproxy/Pelikan claims; "Google web search serving tier" caching. | twitter/twemproxy README; Pelikan project docs; EVCache README and wiki (already verified for module 10); Jeff Dean's WSDM 2009 search-systems talk, if the Google section stays. |
| [23](./23-system-design-chat-app/REAL_WORLD_EXAMPLES.md) | Real-time chat | WhatsApp "2+ billion users, Erlang & FreeBSD"; Netflix push service; Discord architecture. | Discord *How Discord Scaled Elixir to 5,000,000 Concurrent Users* (already verified for module 16) and *Why Discord is switching from Go to Rust*; WhatsApp/Meta newsroom posts for user counts (with dates); Firebase Cloud Messaging docs; Zuul push wiki pages. |
| [24](./24-system-design-video-streaming/REAL_WORLD_EXAMPLES.md) | Video streaming | Netflix "Dynamic Optimizer"; YouTube VP9/transcoding claims. | Netflix's VMAF GitHub repo and research.netflix.com papers; RFC 8216 (HLS); DASH Industry Forum docs; YouTube or Google developer posts on VP9. |
| [25](./25-system-design-rate-limiter/REAL_WORLD_EXAMPLES.md) | Distributed rate limiter | **"Stripe uses atomic Redis sliding windows" conflicts with Stripe's own post, which says token bucket** (verified for module 05). Check Doorman and Cloudflare XDP claims. | Stripe *Scaling your API with rate limiters* (already verified); youtube/doorman README; Cloudflare blog post on L4Drop/XDP; Google Cloud Armor rate-limiting docs; Netflix concurrency-limits README (already verified). |

### Part 6b · Full system designs (32, 34–37) (one PR)

| # | Topic | What to check | Candidate sources |
| :-: | :--- | :--- | :--- |
| [32](./32-rest-api-design-and-idempotency/REAL_WORLD_EXAMPLES.md) | REST API design & idempotency | Already cites 2 sources, but they haven't been checked. Netflix Zuul retry claims. | Stripe idempotency post (already verified for module 29); Google API Improvement Proposals (google.aip.dev); Google Cloud docs on gRPC-HTTP transcoding; Zuul wiki. |
| [34](./34-system-design-news-feed/REAL_WORLD_EXAMPLES.md) | News feed | YouTube home feed, Netflix homepage rows, Twitter timelines, Instagram ranking: four large claims, likely unsourced. | Covington et al., *Deep Neural Networks for YouTube Recommendations* (RecSys 2016); Gomez-Uribe & Hunt, *The Netflix Recommender System* (ACM TMIS 2015); X/Twitter's 2023 recommendation-algorithm post and the twitter/the-algorithm repo; TAO paper (already verified for module 10). |
| [35](./35-system-design-notification-system/REAL_WORLD_EXAMPLES.md) | Notification system | "Netflix Hermes notification platform": check that the name and role are real. | Firebase Cloud Messaging docs; Apple Push Notification service docs; drop the Netflix section if it can't be sourced. |
| [36](./36-system-design-web-crawler/REAL_WORLD_EXAMPLES.md) | Web crawler | Googlebot "planetary crawling" specifics; Heritrix claims. | Google Search Central docs on Googlebot and crawl budget; RFC 9309 (robots.txt); internetarchive/heritrix3 README and docs. |
| [37](./37-system-design-search-autocomplete/REAL_WORLD_EXAMPLES.md) | Search autocomplete | Google Instant claims; "Netflix fuzzy actor typeahead" looks unsourced. | Google's 2010 Google Instant announcement; Elasticsearch completion-suggester docs, or another typeahead engine with public docs, to replace the Netflix section. |

### Part 6c · Full system designs (38–45) (one PR)

| # | Topic | What to check | Candidate sources |
| :-: | :--- | :--- | :--- |
| [38](./38-system-design-cloud-file-storage/REAL_WORLD_EXAMPLES.md) | Cloud file storage & sync | Dropbox Magic Pocket and sync-engine claims; Colossus claims. | dropbox.tech posts *Inside the Magic Pocket* and the 2020 sync-engine rewrite; Google Cloud blog *A peek behind Colossus*. |
| [39](./39-system-design-proximity-service/REAL_WORLD_EXAMPLES.md) | Proximity service | H3 and S2 claims (both have good public docs). | h3geo.org docs and Uber's H3 announcement; s2geometry.io docs. |
| [40](./40-system-design-payment-system/REAL_WORLD_EXAMPLES.md) | Digital wallet & payments | Already cites 4 sources, but they haven't been checked. Check each claim against its link, as was done for modules 01–03. | The existing Stripe and PayPal links. |
| [41](./41-system-design-hotel-reservation/REAL_WORLD_EXAMPLES.md) | Reservation system | Google Hotels and "Netflix live events ticketing" look unsourced; Airbnb state machine. | Airbnb engineering posts on payments idempotency, if readable; PostgreSQL docs on row locks (`SELECT ... FOR UPDATE`) and exclusion constraints as the documented mechanism for preventing double booking. |
| [42](./42-system-design-real-time-gaming-leaderboard/REAL_WORLD_EXAMPLES.md) | Real-time gaming leaderboard | "Netflix Games global ranking" looks unsourced; Riot ranked distribution. | Redis sorted-set docs (the standard leaderboard structure); Google Play Games Services leaderboard docs; Riot's support pages for ranked tiers. |
| [43](./43-system-design-distributed-job-scheduler/REAL_WORLD_EXAMPLES.md) | Distributed job scheduler | "Borg Chronos" naming; Netflix Meson (its blog post blocks automated reading). | Google SRE book chapter *Distributed Periodic Scheduling with Cron*; Verma et al., *Large-scale cluster management at Google with Borg* (EuroSys 2015); conductor-oss/conductor README. |
| [44](./44-system-design-metrics-monitoring-and-alerting/REAL_WORLD_EXAMPLES.md) | Metrics monitoring & alerting | Already cites 3 sources, but they haven't been checked. Monarch and Atlas claims. | Adams et al., *Monarch: Google's Planet-Scale In-Memory Time Series Database* (VLDB 2020); Netflix/atlas README and wiki. |
| [45](./45-system-design-ad-click-aggregation/REAL_WORLD_EXAMPLES.md) | Ad click aggregation | Google Photon claims; Netflix Keystone (blog blocks automated reading). | Ananthanarayanan et al., *Photon: Fault-tolerant and Scalable Joining of Continuous Data Streams* (SIGMOD 2013); Apache Flink docs on windows and exactly-once processing; Kafka docs. |

## Suggested order

1. **Part 5** (17–20, 33): concept-heavy, with many good primary sources (papers, docs).
2. **Part 0** (26–28): short, and fixes a likely error in module 28.
3. **Part 6** in three PRs (6a, 6b, 6c), about five modules each, so each review stays manageable.
