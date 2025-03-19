from app.tasks import celery_app  # TODO: this whole file seems to be unused, or i don't understand how it works

if __name__ == "__main__":
    celery_app.start()
