from django.apps import AppConfig


class DaVinciCrawlingSchedulerConfig(AppConfig):
    name = 'davinci_crawling.scheduler'
    verbose_name = "Scheduler of Django DaVinci Crawling"

    scheduler = None

    def ready(self):
        pass
        # if self.scheduler is None:
        #    from davinci_crawling.scheduler.scheduler import Scheduler
        #    # Starting the scheduler
        #    self.scheduler = Scheduler.get()
        #    self.scheduler.start_schedule()
