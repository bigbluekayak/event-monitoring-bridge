import os
import redis
from redis import Redis
from rq import Queue, Connection
from rq.worker import HerokuWorker as Worker
from urllib.parse import urlparse


listen = ['high', 'default', 'low']

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise RuntimeError("Set up Heroku Data For Redis first, \
    make sure its config var is named 'REDIS_URL'.")

url = urlparse(os.environ.get("REDIS_URL"))
r = Redis(host=url.hostname, port=url.port, password=url.password, ssl=True, ssl_cert_reqs=None)

if __name__ == '__main__':
    with Connection(r):
        worker = Worker(map(Queue, listen))
        worker.work()