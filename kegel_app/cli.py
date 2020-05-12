from kegel_app.app import KegElApp


def cli_entry():
    KegElApp.cli.main()


@KegElApp.cli.command('verify-translations', help='Verifies all strings marked for translation')
def verify_translations():
    from pathlib import Path
    from morphi.messages.validation import check_translations

    root_path = Path(__file__).resolve().parent.parent
    check_translations(
        root_path,
        'keg_elements',
    )


if __name__ == '__main__':
    cli_entry()
