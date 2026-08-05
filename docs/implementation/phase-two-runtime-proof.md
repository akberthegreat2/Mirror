# Phase two runtime proof

Phase two introduces the first real workload path:

- crawl a site
- persist discovered URLs
- store page blobs when requested
- schedule the crawl again later
- run the job through a worker backend
- keep metadata separate from blobs

The goal is not to add every backend in the world.
The goal is to prove that Mirror can do the minimum real job end to end.
