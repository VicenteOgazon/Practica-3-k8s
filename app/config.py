import os

class Config:
    INSTANCE_NAME = os.getenv("INSTANCE_NAME")
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


class DevelopmentConfig(Config):
    USE_CACHE = False

class ProductionConfig(Config):
    USE_CACHE = True