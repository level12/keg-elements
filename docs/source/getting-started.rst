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


Upgrade Notes
=============

While we attempt to preserve backward compatibility, some KegElements versions do introduce
breaking changes. This list should provide information on needed app changes.

- 0.8.0
  - ``pytest`` removed support for nose-style methods, so base test classes (e.g. ``EntityBase``)
  now use ``setup_method`` instead of ``setup``
  - Bootstrap 4 "horizontal" form templates had been broken and were displaying forms in the
  vertical style instead. This has been resolved, which means forms will change to showing with
  horizontal layout. If this is not desired, you will need to override the form templates/macros.
  - Tab index setting has been removed from the form macro templates. tabindex > 0 is not
  recommended for accessibility. The _field_order attribute of the form should be used to
  indirectly control tab order, instead of setting tabindex explicitly.
  - Template files now follow keg's more recent naming scheme to use dashes instead of underscores.
  E.g. ``keg_elements/forms/horizontal_b4.html`` became ``keg-elements/forms/horizontal-b4.html``
  - The older Bootstrap 3 macro template (``horizontal.html``) has been renamed for
  namespacing to ``horizontal-b3.html``.
  - ``keg-elements/form-view.html`` and ``keg-elements/grid-view.html`` are now available, but
  need a config value (either ``BASE_TEMPLATE`` or ``KEG_BASE_TEMPLATE``) set to represent the
  parent to extend.
  - forms now have an ident field built-in to assist in identifying the form from POSTed data.
  If a form's render is customized in the template layer, the ident field may be missing. A few
  options for moving forward:

    - add the field in render (identified by the result of the form's ``_form_ident_key`` method)
    - turn off ident validation by setting ``_form_ident_strict`` to ``False`` on the form class
    - turn off the field by setting ``_form_ident_enabled`` to ``False`` on the form class
