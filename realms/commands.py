import argparse
import pbr.version

from realms import config
from realms import create_app


def dev(port, host):
    """ Run development server
    """
    print("Starting development server")

    config_path = config.get_path()
    if config_path:
        print("Using config: %s" % config_path)
    else:
        print("Using default configuration")

    create_app().run(host=host,
                     port=port,
                     debug=True)


def main():
    version = pbr.version.VersionInfo('realms_wiki').version_string()
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default=config.HOST,
                        help='Host IP to listen on')
    parser.add_argument('--port', type=int, default=config.PORT,
                        help='TCP port to listen on')
    parser.add_argument('--version', action='version', version="%s" % version)
    args = parser.parse_args()
    dev(args.port, args.host)


if __name__ == '__main__':
    main()
