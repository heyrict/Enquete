Enquete
=======
A kivy-based application for better
handling simple-table constraints.

Usage
-----

### Basical Usage
1. Open a `.pmdf` file
2. Edit!

Notice: You can only create **ONE Table** with a pmdf file.

### PMDF File Format
A text format of `.pmdf` is provided which functions
as a schema like in RDBs.

Every line in the pmdf file indicates a field with the given format below:

```
[field_name]  [type]  [format1 [format2]]
```

For example, an emploee table may look like this:

```
ID          int      not_null
age         int      [18,80]    not_null
occupation  str      ['manager','worker','boss','secretary']  not_null
```

Supported formats and constraints:

|       Type       | regex | not_null | num_range | str_range |
|------------------|-------|----------|-----------|-----------|
|       str        |   o   |    o     |     x     |     o     |
| int/double/float |   x   |    o     |     o     |     x     |


Compile
-------
You must have the following things to compile this program:

- [python3](http://www.python.org)
- [kivy](http://github.com/kivy/kivy)
- Android SDK
- Android NDK
- Apache Ant
- buildozer

After all the dependencies are installed,
you can run `buildozer android debug` to build a
debug version, or `buildozer android release` to
build a release version.

Contribute
----------
1. Folk this program to your own repository
2. Add a new branch indicating your changes to make.
3. Clone your folk to your local machine.
4. Do some changes.
5. Push your changes to your folked git repository.
6. Add a new pull request.
