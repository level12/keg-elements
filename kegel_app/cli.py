from kegel_app.app import KegElApp


def cli_entry():
    KegElApp.cli.main()


if __name__ == '__main__':
    cli_entry()
