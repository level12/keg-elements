Getting Started
===============

.. contents::
    :local:

.. _gs-install:

Installation
------------

- Bare functionality: ``pip install kegelements``
- Internationalization extensions: ``pip install kegelements[i18n]``


.. _gs-templates:

Templates
---------

Jinja templates are made available for rendering forms. To have these included in a keg
app, include the core blueprint in the app::

    from keg import Keg
    from keg_elements.core import keg_element_blueprint

    from my_app.views import public_bp, private_bp

    class MyApp(Keg):
        import_name = 'my_app'
        use_blueprints = [public_bp, private_bp, keg_element_blueprint]

Note, if you are using `keg-auth` in your app, the above is not required. That library pulls
in the templates to support auth views.


.. _gs-model:

Data Model
----------

KegElements provides model mixins with helpful default columns and methods::

    from keg.db import db
    from keg_elements.db.mixins import DefaultMixin

    class Thing(DefaultMixin, db.Model):
        __tablename__ = 'things'

        # id, created_utc, updated_utc provided via mixin
        # tests can use Thing.testing_create to get an instance with random data

        name = db.Column(db.Unicode(50), nullable=False)
        color = db.Column(db.Unicode)


.. _gs-forms:

Forms
-----

KegElements extends wtforms-alchemy model form generation with some custom fields, an
optional meta info override, and additional validation::

    from keg_elements.forms import FieldMeta, ModelForm, form_validator
    from my_app.model import entities as ents

    class RelatedThingForm(ModelForm):
        class Meta:
            model = ents.RelatedThing
            include_foreign_keys = True

        class FieldsMeta:
            name = FieldMeta('Fancy Label')

        @form_validator
        def validate_name(self):
            # do validation here


.. _gs-i18n:

Internationalization
--------------------

KegElements supports `Babel`-style internationalization of text strings through the `morphi` library.
To use this feature, specify the extra requirements on install::

    pip install kegelements[i18n]

Currently, English (default) and Spanish are the supported languages in the UI.

Helpful links
^^^^^^^^^^^^^

 * https://www.gnu.org/software/gettext/manual/html_node/Mark-Keywords.html
 * https://www.gnu.org/software/gettext/manual/html_node/Preparing-Strings.html


Message management
^^^^^^^^^^^^^^^^^^

The ``setup.cfg`` file is configured to handle the standard message extraction commands. For ease of development
and ensuring that all marked strings have translations, a tox environment is defined for testing i18n. This will
run commands to update and compile the catalogs, and specify any strings which need to be added.

The desired workflow here is to run tox, update strings in the PO files as necessary, run tox again
(until it passes), and then commit the changes to the catalog files.

.. code::

    tox -e i18n
