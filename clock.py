import event_monitoring_logs
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=60)
def timed_job():
    event_monitoring_logs.process.delay()


sched.start()