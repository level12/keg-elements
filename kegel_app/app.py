from keg.app import Keg
import keg.db

from kegel_app.extensions import Grid
from kegel_app.views import keg_element_blueprint


class KegElApp(Keg):
    import_name = 'kegel_app'
    keyring_enable = False
    use_blueprints = [keg_element_blueprint]
    db_enabled = True

    def on_init_complete(self):
        Grid.manager.init_db(keg.db.db)
        Grid.manager.init_app(self)
