Changelog
=========

0.12.0 released 2024-06-28
--------------------------

- support python 3.12 (2fcecec_)
- update sentry integration to support Sentry SDK 2+ (b40e3c8_)

.. _2fcecec: https://github.com/level12/keg-elements/commit/2fcecec
.. _b40e3c8: https://github.com/level12/keg-elements/commit/b40e3c8


0.11.0 released 2024-01-16
--------------------------

- use sentry SDK for cron monitor setup and check-ins (405f677_)

.. _405f677: https://github.com/level12/keg-elements/commit/405f677


0.10.0 released 2023-12-01
--------------------------

- flake8 fixes in tests (f6d862e_)
- support wtforms 3.1 change to choices iteration (3ec5abe_)

.. _f6d862e: https://github.com/level12/keg-elements/commit/f6d862e
.. _3ec5abe: https://github.com/level12/keg-elements/commit/3ec5abe


0.9.1 released 2023-05-22
-------------------------

- support monitoring jobs with Sentry (8bd9cb5_)

.. _8bd9cb5: https://github.com/level12/keg-elements/commit/8bd9cb5


0.9.0 released 2023-03-03
-------------------------

- support SQLAlchemy 2.0 (fce6248_)
- support keg testing app context changes (4122e9e_)
- fixed upgrade notes in documentation (514b8ff_)

.. _fce6248: https://github.com/level12/keg-elements/commit/fce6248
.. _4122e9e: https://github.com/level12/keg-elements/commit/4122e9e
.. _514b8ff: https://github.com/level12/keg-elements/commit/514b8ff


0.8.0 released 2022-12-12
-------------------------

- fix select2 inclusion in form view template, document template updates (d01f7dc_)
- support rendering WTForms form fields (e0e3136_)
- resolve radio ID duplication and error display in Bootstrap 4 (74b7215_)
- **BC break** change oid kwarg in MethodsMixin.edit to _oid (4d67937_)
- **BC break** replace testing_create with fake, for brevity (747d208_)
- drop remaining python 2 support and six usage (decd030_)
- add stable requirements set for CI (1fbcea4_)
- **BC break** drop tabindex explicit arguments from form macro templates (09c4e8b_)
- add generic form-view.html and grid-view.html templates (1eb8db2_)
- fix Bootstrap 4 usage for horizontal forms (57fc4ab_)
- build in datetime form controls helper, namespaced for keg-elements (d098f07_)
- change form-level error class used to one Bootstrap 4 will display (55b9c67_)
- allow passing name and/or id to form in form macro (fe1ac26_)
- enable skipped sqlite tests and fix session breakage (90e2d88_)
- add a form ident field to the keg-elements base form (941e4a7_)
- add query-level insert/update methods to supplement ORM-level add/edit (60fac30_)
- prevent select box choices filtered improperly when no query applied (aef1cf0_)
- handle SA ORM attributes and hybrid properties for relationship form fields (97244de_)
- resolve library warnings and deprecations (9ecb616_)

.. _d01f7dc: https://github.com/level12/keg-elements/commit/d01f7dc
.. _e0e3136: https://github.com/level12/keg-elements/commit/e0e3136
.. _74b7215: https://github.com/level12/keg-elements/commit/74b7215
.. _4d67937: https://github.com/level12/keg-elements/commit/4d67937
.. _747d208: https://github.com/level12/keg-elements/commit/747d208
.. _decd030: https://github.com/level12/keg-elements/commit/decd030
.. _1fbcea4: https://github.com/level12/keg-elements/commit/1fbcea4
.. _09c4e8b: https://github.com/level12/keg-elements/commit/09c4e8b
.. _1eb8db2: https://github.com/level12/keg-elements/commit/1eb8db2
.. _57fc4ab: https://github.com/level12/keg-elements/commit/57fc4ab
.. _d098f07: https://github.com/level12/keg-elements/commit/d098f07
.. _55b9c67: https://github.com/level12/keg-elements/commit/55b9c67
.. _fe1ac26: https://github.com/level12/keg-elements/commit/fe1ac26
.. _90e2d88: https://github.com/level12/keg-elements/commit/90e2d88
.. _941e4a7: https://github.com/level12/keg-elements/commit/941e4a7
.. _60fac30: https://github.com/level12/keg-elements/commit/60fac30
.. _aef1cf0: https://github.com/level12/keg-elements/commit/aef1cf0
.. _97244de: https://github.com/level12/keg-elements/commit/97244de
.. _9ecb616: https://github.com/level12/keg-elements/commit/9ecb616


0.7.2 released 2022-03-04
-------------------------

- adjust form mixin interface to clarify methods related to forms and make overrides easier (2a326b5_)

.. _2a326b5: https://github.com/level12/keg-elements/commit/2a326b5


0.7.1 released 2022-03-04
-------------------------

- add method errors out on invalid field name (9511f73_)

.. _9511f73: https://github.com/level12/keg-elements/commit/9511f73


0.7.0 released 2022-03-04
-------------------------

- add base class/mixin for form views (fcf8f02_)
- multiselect field will not coerce every option to an object, performance issue (0ccd609_)
- edit method errors out on invalid field name (98ad0b0_)
- factor test column data skipping (639bcb8_)
- support SA column properties in test data generation (1148633_)
- support WTForms 3.0.0 with form-level validation errors, field flags changes (794ce75_)

.. _fcf8f02: https://github.com/level12/keg-elements/commit/fcf8f02
.. _0ccd609: https://github.com/level12/keg-elements/commit/0ccd609
.. _98ad0b0: https://github.com/level12/keg-elements/commit/98ad0b0
.. _639bcb8: https://github.com/level12/keg-elements/commit/639bcb8
.. _1148633: https://github.com/level12/keg-elements/commit/1148633
.. _794ce75: https://github.com/level12/keg-elements/commit/794ce75


0.6.0 released 2021-09-10
-------------------------

Note: due to the form field description change listed below, JS popover usage
from the previous UX can be removed from apps.

- Move form field descriptions to be more visible (f7a287e_)
- Resolve jinja2 Markup deprecation (86cfe0e_)
- Adds column check to verify date/time defaults are not set to an instantiated value Fixes #149 (d8489d1_)
- Drop python 3.6 from testing, add 3.9 (93ee3df_)
- Support webgrid form posts in GridView (requires webgrid's form args loader) (b945bb4_)

.. _f7a287e: https://github.com/level12/keg-elements/commit/f7a287e
.. _86cfe0e: https://github.com/level12/keg-elements/commit/86cfe0e
.. _d8489d1: https://github.com/level12/keg-elements/commit/d8489d1
.. _93ee3df: https://github.com/level12/keg-elements/commit/93ee3df
.. _b945bb4: https://github.com/level12/keg-elements/commit/b945bb4


0.5.30 released 2021-02-02
--------------------------

- Add magnitude/range/type directives for random number generation in testing (a9ca44f_)
- Set up documentation on readthedocs.io (f68c812_)

.. _a9ca44f: https://github.com/level12/keg-elements/commit/a9ca44f
.. _f68c812: https://github.com/level12/keg-elements/commit/f68c812


0.5.29 released 2021-01-29
--------------------------

- Add RelationshipField and RelationshipMultipleField for generating select fields from ORM (8d90b5a_)
- Add form meta option include_required_foreign_keys for form generation (8d90b5a_)
- Add standard testing FormBase for field verification (2b0ee8a_)
- Allow model form subclasses to utilize the super's FieldsMeta (84dcc1f_)
- Use blank FieldMeta object by default when no meta is given (2457605_)
- Provide a model mixin for generic id/value lookup tables (a392941_)
- Add testing_set_related entity method to wrap related object creation (e6fe3d9_)

.. _8d90b5a: https://github.com/level12/keg-elements/commit/8d90b5a
.. _2b0ee8a: https://github.com/level12/keg-elements/commit/2b0ee8a
.. _84dcc1f: https://github.com/level12/keg-elements/commit/84dcc1f
.. _2457605: https://github.com/level12/keg-elements/commit/2457605
.. _a392941: https://github.com/level12/keg-elements/commit/a392941
.. _e6fe3d9: https://github.com/level12/keg-elements/commit/e6fe3d9


0.5.28 released 2020-11-13
--------------------------

- Auto-generate form field options for enum columns (a074cd2_)
- Fix mssql CI (4ec0480_)
- Fix test model key cascade (53dd792_)
- Fix update_collection for models with unique constraints (900f3ec_)

.. _a074cd2: https://github.com/level12/keg-elements/commit/a074cd2
.. _4ec0480: https://github.com/level12/keg-elements/commit/4ec0480
.. _53dd792: https://github.com/level12/keg-elements/commit/53dd792
.. _900f3ec: https://github.com/level12/keg-elements/commit/900f3ec


0.5.27 released 2020-06-09
--------------------------

- Properly handle missing or empty config keys in Sentry filtering (bfb413b_)

.. _bfb413b: https://github.com/level12/keg-elements/commit/bfb413b


0.5.26 released 2020-06-09
--------------------------

- Upgrade Sentry library and improve filtering of sensitive data in error reports (5c0afad_)
- Add alembic helper functions for common tasks (9440a4e_)
- Require numeric columns to specify scale and precision (d0e0260_)
- Improve form-level error handling (e590f2d_)

.. _5c0afad: https://github.com/level12/keg-elements/commit/5c0afad
.. _9440a4e: https://github.com/level12/keg-elements/commit/9440a4e
.. _d0e0260: https://github.com/level12/keg-elements/commit/d0e0260
.. _e590f2d: https://github.com/level12/keg-elements/commit/e590f2d


0.5.25 released 2020-05-12
--------------------------

- check translations in CI (3a01a93_)
- add GridView for convenient webgrid usage (a9deb06_)
- support wtforms 2.3+ (0d78557_)
- remove pytest from non-testing code (5e11b79_)

.. _3a01a93: https://github.com/level12/keg-elements/commit/3a01a93
.. _a9deb06: https://github.com/level12/keg-elements/commit/a9deb06
.. _0d78557: https://github.com/level12/keg-elements/commit/0d78557
.. _5e11b79: https://github.com/level12/keg-elements/commit/5e11b79


0.5.24 released 2020-03-23
--------------------------

- select all/none feature for MultiCheckbox fields (vanilla JS) (7a727b6_)

.. _7a727b6: https://github.com/level12/keg-elements/commit/7a727b6


0.5.23 released 2020-03-20
--------------------------

- enable MultiCheckboxField usage in templates for bootstrap 3 (c1dba1b_)
- fix SA arrow column default timezone (3eea89d_)

.. _c1dba1b: https://github.com/level12/keg-elements/commit/c1dba1b
.. _3eea89d: https://github.com/level12/keg-elements/commit/3eea89d


0.5.22 released 2020-02-27
--------------------------

- Add missing class to checkbox input (4b4e44c_)

.. _4b4e44c: https://github.com/level12/keg-elements/commit/4b4e44c


0.5.21 released 2020-02-21
--------------------------

- Add support for multi select checkbox form fields (fa21fa4_)
- allow columns to override their random data generation (a3445c1_)

.. _fa21fa4: https://github.com/level12/keg-elements/commit/fa21fa4
.. _a3445c1: https://github.com/level12/keg-elements/commit/a3445c1


0.5.20 released 2020-02-03
--------------------------

- Fix BS4 Field Description (a9d3479_)

.. _a9d3479: https://github.com/level12/keg-elements/commit/a9d3479


0.5.19 released 2019-11-19
--------------------------

- Adds a U.S. state select field (3abd696_)
- Add type hint widget for use with form text inputs (fe089e0_)
- Use recommended classes and tag layout for rendering bootstrap 4 checkboxes (d20b084_)
- Add Python 3.8 support and drop support for Python 3.5 (d87b2db_)
- Exclude create/update timestamp fields from model form generation by default (012fe38_)

.. _3abd696: https://github.com/level12/keg-elements/commit/3abd696
.. _fe089e0: https://github.com/level12/keg-elements/commit/fe089e0
.. _d20b084: https://github.com/level12/keg-elements/commit/d20b084
.. _d87b2db: https://github.com/level12/keg-elements/commit/d87b2db
.. _012fe38: https://github.com/level12/keg-elements/commit/012fe38


0.5.18 released 2019-08-05
--------------------------

- Prevent double rendering of hidden form inputs in template macros (e0b47dc_)

.. _e0b47dc: https://github.com/level12/keg-elements/commit/e0b47dc


0.5.17 released 2019-07-29
--------------------------

- Skip arrow fields during form generation if default value set (95e26a6_)
- Add bootstrap 4 form template option (bc4efcd_)

.. _95e26a6: https://github.com/level12/keg-elements/commit/95e26a6
.. _bc4efcd: https://github.com/level12/keg-elements/commit/bc4efcd


0.5.16 released 2019-07-09
--------------------------

- db: Add SoftDeleteMixin (ebc25b9_)
- Enable Manual Ordering of Form Fields (#101) (00ce0b6_)
- Merge pull request #103 from level12/pre-commit-hook-setup (68b92d6_)

.. _ebc25b9: https://github.com/level12/keg-elements/commit/ebc25b9
.. _00ce0b6: https://github.com/level12/keg-elements/commit/00ce0b6
.. _68b92d6: https://github.com/level12/keg-elements/commit/68b92d6


0.5.15 released 2019-07-02
--------------------------

- Add base class for enum types used by database entities (49e4cf3_)
- Improve random number generation in testing defaults for numeric columns (25321c1_)

.. _49e4cf3: https://github.com/level12/keg-elements/commit/49e4cf3
.. _25321c1: https://github.com/level12/keg-elements/commit/25321c1


0.5.14 released 2019-06-28
--------------------------

- Add features to form's FieldMeta overrides and improve support for enum columns in model forms (c7ddf0d_)
- Drop 2.7 support and add 3.7 support (c7ddf0d_)
- Fix spelling errors (be0334f_)

.. _c7ddf0d: https://github.com/level12/keg-elements/commit/c7ddf0d
.. _be0334f: https://github.com/level12/keg-elements/commit/be0334f


0.5.13 released 2019-06-17
--------------------------

- Add additional testing helpers and fix float field form generation issue (4b725fd_)

.. _4b725fd: https://github.com/level12/keg-elements/commit/4b725fd


0.5.12 released 2019-02-07
--------------------------

- Fix Deprecation Warnings and Remove Wheelhouse (7af6f55_)

.. _7af6f55: https://github.com/level12/keg-elements/commit/7af6f55


0.5.11 released 2018-11-20
--------------------------

- Switch yield tests to loops to resolve pytest warning (a3e1b5c_)

.. _a3e1b5c: https://github.com/level12/keg-elements/commit/a3e1b5c


0.5.10 released 2018-11-13
--------------------------

- Added template support for adding tab indexes when creating wtforms (f36997e_)
- Add support for multiple-column keys in ColumnCheck (8dc840b_)
- Add optional i18n support using morphi (46229a4_)

.. _f36997e: https://github.com/level12/keg-elements/commit/f36997e
.. _8dc840b: https://github.com/level12/keg-elements/commit/8dc840b
.. _46229a4: https://github.com/level12/keg-elements/commit/46229a4


0.5.9 released 2018-09-19
-------------------------

- FEAT: Add additional metadata to the results of Form.fields_todict (2f863f1_)

.. _2f863f1: https://github.com/level12/keg-elements/commit/2f863f1


0.5.8 released 2018-07-19
-------------------------

- Merge pull request #82 from level12/add-alphanumeric-validator (bbf43ec_)

.. _bbf43ec: https://github.com/level12/keg-elements/commit/bbf43ec


0.5.7 released 2018-06-19
-------------------------

- Merge pull request #80 from level12/check-for-missing-app-ctx (1d0f3d8_)

.. _1d0f3d8: https://github.com/level12/keg-elements/commit/1d0f3d8


0.5.6 released 2018-04-30
-------------------------

- FEAT: Automatically generate range validators for numeric fields in `ModelForm`\ s (48a3827_)
- Improvements to the uniqueness form validator (29937c5_)

.. _48a3827: https://github.com/level12/keg-elements/commit/48a3827
.. _29937c5: https://github.com/level12/keg-elements/commit/29937c5


0.5.5 released 2018-04-25
-------------------------

- FEAT: Add custom Sentry client to filter out flask config object from reports (927e012_)

.. _927e012: https://github.com/level12/keg-elements/commit/927e012


0.5.4 released 2017-08-08
-------------------------

- Use pyp to manage releases (5b11356_)
- FEAT: Add file/stream encryption methods (aeab61a_)

.. _5b11356: https://github.com/level12/keg-elements/commit/5b11356
.. _aeab61a: https://github.com/level12/keg-elements/commit/aeab61a


0.5.3 - 2017-04-26
------------------

* FEAT: Add DontCare for Easy Testing (28643d6_)

.. _28643d6: https://github.com/level12/keg-elements/commit/28643d6


0.5.2 - 2017-03-23
------------------

* FEAT: Add additional utility functions (2e27a60_)
* BUG: Check all records when updating a collection (fffb7c8_)

.. _2e27a60: https://github.com/level12/keg-elements/commit/2e27a60
.. _fffb7c8: https://github.com/level12/keg-elements/commit/fffb7c8


0.5.0 - 2016-12-19
-------------------

* FEAT: Create crypto primitives (5a981b5_)
* Refactor testing_create kwargs validation and ignore "_" prefixed keys (484d032_)

.. _5a981b5: https://github.com/level12/keg-elements/commit/5a981b5
.. _484d032: https://github.com/level12/keg-elements/commit/484d032


0.4.2 - 2016-11-11
------------------

* FEATURE: Verify kwargs correspond to columns and relationships in `testing_create`. (db533dd_)
* FEATURE: Add support for form-level validation. (GH-53_)

.. _db533dd: https://github.com/level12/keg-elements/commit/db533dd
.. _GH-53: https://github.com/level12/keg-elements/pull/53


0.4.1 - 2016-10-19
------------------

* Add unique form validator (a0c7447_)

.. _a0c7447: https://github.com/level12/keg-elements/commit/a0c7447


0.4.0 - 2016-09-08
------------------

* FEATURE: Port ``MethodsMixin`` with a number of helpful functions when working with
  SQLAlchemy ORM entities. (GH-49_, GH-51_)
* FEATURE: Add a new TimeZone Column. (GH-50_)

* MAINTENANCE: Provide better testing support for polymorphic SQLAlchemy
  ORM entities. (GH-47_)

* BUG: Fix descriptions when implicitly rendering checkboxes (GH-48_)

.. _GH-50: https://github.com/level12/keg-elements/pull/50
.. _GH-51: https://github.com/level12/keg-elements/pull/51
.. _GH-49: https://github.com/level12/keg-elements/pull/49
.. _GH-48: https://github.com/level12/keg-elements/pull/48
.. _GH-47: https://github.com/level12/keg-elements/pull/47


0.3.2 - 2016-08-03
------------------
* Support `dirty_check` flag on form objects (GH-46_)

.. _GH-46: https://github.com/level12/keg-elements/pull/46


0.3.1
------

* Allow FieldMeta to override default widget and add extra validators (GH-38)
* Allow customization of readonly and disabled attributes on input, select, and radio fields (GH-37)
* Improve the logic for when to default a form field to RequiredBoolRadioField (GH-36)
* Upgrades to the CI Environment

0.3.0
-----

* Allow static renders to be configured with custom macros. (GH-34)
* Synchronize static templates with dynamic templates. (GH-31)
* You can now give a field a description with a string or callback. (GH-23, GH-22)
* Introduced a RequiredBoolRadioField for use with boolean columns. (GH-25)
* Support randomly filling EmailTypes. (GH-24)
* Support additional parameters for randomizing integers. (GH-19)
* ``testing_create`` will randomly select a boolean value for SQLAlchemy boolean
  fields. (GH-28)
* We now have a working CI. (GH-27)
* Constraint tests will fail if all fields are not covered. (GH-21)
* Introduced a new form-upload macro. (GH-18)
* Static render now uses element.data unless it is a SelectField (GH-16)
* ``MethodsMixin`` has a new ``to_dict`` method. (d83d93f)
* ``MethodsMixin`` has a new ``ensure`` method. (e5687ed)


* Fix bug where static renders would not output the label. (GH-33)
* Fix property names when using automatic test cases. (GH-29)
* Fix issue where we wouldn't use a consistent json parser. (GH-13)
* Fix a bug where polymorphic columns are included in ``testing_create``. (147c23)


development version: 2015-07-28
-------------------------------

* Add db.mixins with DefaultColsMixin (id, Arrow lib UTC timestamps) and MethodsMixin (incomplete).
* Some MethodsMixin methods now have support for commit/flush parameters.
* Add .testing:EntityBase which uses named tuples to declare the checks needed and adds some
  additional logic.
