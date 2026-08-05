# Scheduling

Mirror can run jobs immediately or on a schedule.

A schedule says:

- what should run
- when it should run
- whether it repeats
- whether it is paused

Why this matters:

- crawlers and monitors usually run again and again
- scheduling lets you build recurring jobs without custom cron scripts
- workers can pull due jobs and execute them safely

A simple schedule might say:

> Crawl `https://example.com` every six hours and save the URLs it finds.
