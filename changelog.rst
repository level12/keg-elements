Changelog
=========

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
