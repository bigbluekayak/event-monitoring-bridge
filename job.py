from rq import Queue
from redis import Redis
from utils import count_words_at_url
import time
from urllib.parse import urlparse
import os

# Tell RQ what Redis connection to use

url = urlparse(os.environ.get("REDIS_URL"))
r = Redis(host=url.hostname, port=url.port, password=url.password, ssl=True, ssl_cert_reqs=None)

q = Queue(connection=r)  # no args implies the default queue

# Delay execution of count_words_at_url('http://nvie.com')
job = q.enqueue(count_words_at_url, 'http://nvie.com')
print(job.result)   # => None  # Changed to job.return_value() in RQ >= 1.12.0

# Now, wait a while, until the worker is finished
time.sleep(2)
print(job.result)   # => 889  # Changed to job.return_value() in RQ >= 1.12.0