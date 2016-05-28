import falcon

from realms.modules import wiki


def main():
    application = falcon.API()

    wiki.WikiRoutes(application)

    return application
