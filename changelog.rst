Changelog
=========

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
  SQLAlchemy ORM entites. (GH-49_, GH-51_)
* FEATURE: Add a new TimeZone Column. (GH-50_)

* MAINTENANCE: Provide better testing support for polymorphic SQLAlchemy
  ORM entities. (GH-47_)

* BUG: Fix descripions when implicitly rendering checkboxes (GH-48_)

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
* Syncronize static templates with dynamic templates. (GH-31)
* You can now give a field a description with a string or callback. (GH-23, GH-22)
* Introduced a RequiredBoolReadioField for use with boolean columns. (GH-25)
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


* Fix bug where static renderes whould not output the label. (GH-33)
* Fix property names when using automatic test cases. (GH-29)
* Fix issue where we wouldn't use a consistent json parser. (GH-13)
* Fix a bug where polymorphic columns are included in ``testing_create``. (147c23)


development version: 2015-07-28
-------------------------------

* Add db.mixins with DefaultColsMixin (id, Arrow lib UTC timestamps) and MethodsMixin (incomplete).
* Some MethodsMixin methods now have support for commit/flush parameters.
* Add .testing:EntityBase which uses named tuples to declare the checks needed and adds some
  additional logic.
