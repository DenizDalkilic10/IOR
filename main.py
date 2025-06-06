from apscheduler.schedulers.blocking import BlockingScheduler
from config import POST_HOUR, POST_MINUTE, MORNING_POST_HOUR, MORNING_POST_MINUTE
from jobs import post_reel_job, post_image_job

if __name__ == '__main__':
    # post_reel_job()
    post_image_job()
    # sched = BlockingScheduler(timezone='Europe/Amsterdam')
    # # sched.add_job(post_image_job, 'cron', day='1-31/2', hour=POST_HOUR, minute=POST_MINUTE)
    # sched.add_job(post_image_job, 'cron', day='1-31/2', hour=MORNING_POST_HOUR, minute=MORNING_POST_MINUTE)
    # # sched.add_job(post_image_job, 'cron', day='2-30/2', hour=MORNING_POST_HOUR, minute=MORNING_POST_MINUTE)
    # # sched.add_job(post_weekly_favorites_job, 'cron', day_of_week='mon', hour=POST_HOUR, minute=POST_MINUTE)
    # sched.start()
