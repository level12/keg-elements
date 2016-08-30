from keg.app import Keg
from keg_elements.core import keg_element_blueprint


class KegElApp(Keg):
    import_name = 'kegel_app'
    keyring_enable = False
    use_blueprints = [keg_element_blueprint]
    db_enabled = True
