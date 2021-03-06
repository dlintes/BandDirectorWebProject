import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    #MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[WebApp]'
    FLASKY_MAIL_SENDER = 'WebApp Admin <webapp@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    UPLOAD_FOLDER = r''
    DOWNLOAD_FOLDER = r''

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        "mysql+pymysql://root:root@localhost:3306/web"

class TestingConfig(Config):
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
    #   'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        "mysql+pymysql://root:root@localhost:3306/web"

class ProductionConfig(Config):
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
     #   'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        "mysql+pymysql://root:root@localhost:3306/web"

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
