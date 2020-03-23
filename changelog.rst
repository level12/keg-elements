Changelog
=========

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
