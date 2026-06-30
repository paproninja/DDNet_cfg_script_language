# DDNet Cfg Script Language

DDNet CFG Script Language (DCSL) it's a declarative language designed to automatically generate `.cfg` files and folder structures for DDNet.


The compiler takes a text file with a `JSON` similar syntax and parses and generates the structure.

---

# Syntax

Strings are written between single quotes, since cfgs can contain double quotes.

```text
'hello'
```

Objects are written between curly brackets.

```text
{
    key: 'value'
    key2: 'value2'
}
```

Lists are written between square brackets.

```text
[
    'value1'
    'value2'
]
```
```text
['value1', 'value2']
```

Commas are optional and the compiler will ignore them. The compiler its not strict with format: You can write properties by lines with indents, as well as you can write properties in the same line.

---

# Root object

The file always starts with a root object. Normally you will define a `folders` property so you can put your `cfg` system inside and organized, but nothing stops you from defining files right away.

Example:

```text
{
    _path: '/home/pablo/.local/share/ddnet/'

    folders: [
        ...
    ]
}
```

---

# Global variables

To define constants, write a property starting by `_` followed by the name. The variable will be saved without the `_` and can be called with `$name`. They can be defined in any abstraction level of folders.

Example:

```text
{
    _color: '5635968'
    _mainname: 'name'
    
    folders: [
        name: 'myfolder'
        _cnstinfolder: 'value'
    ]
}
```

There are 2 special constants: `$ROOT` and `$PATH`.

`$ROOT` must be defined on the root object, and will refer to the absolute path of the game folder:

```text
_ROOT: '/home/user/.local/share/ddnet/'
```

or in Windows:

```text
_ROOT: 'C:\\Users\user\AppData\Roaming\DDNet\'
```

`$PATH` must not be defined, and it will return the relative path stack. For example, using it in `folder1/folder2/file.cfg`, it will return `folder1/folder2`.
The variable is used internally to fill relative paths, but can also be called if needed.

---

# Folders

Folders internally only create the path for the file to follow, the folder wont be created if there arent any files inside.

Properties:

| Property | Type   | Forced |
|----------|--------|--------|
| name     | string | Yes    |
| folders  | array  | No     |
| files    | array  | No     |

Example:

```text
{
    name: 'menu'

    folders: [
        ...
    ]

    files: [
        ...
    ]
}
```

---

# Files

Files create real files in your game files. Extensions aren't added to the name automatically.

Properties:

| Property | Type             | Forced |
|----------|------------------|--------|
| name     | string           | Yes    |
| command  | string / array   | No     |
| bind     | array of objects | No     |
| unbind   | string / array   | No     |
| echo     | array            | No     |

You can make your own properties, by defining them in the compiler.

Example:
```text
{
    name: 'menu.cfg'
    command: `player_name name`
}
```

---

# Properties

## command

It inserts a command directly in the file, without any processing. Use $ to insert variables.
It can be a string or an array of strings.

Example:

```text
command: 'echo hello; player_color_body 255'
```

Example:

```text
command: [
    'line1'
    'line2'
    '$variable'
]
```

Results in:

```cfg
line1
line2
variable value
```

---

## unbind

Generates `unbind <key>`
It can be a string or an array of strings.

Example:

```text
unbind: [
    '1'
    '2'
    'space'
]
```

Results in:

```cfg
unbind 1
unbind 2
unbind space
```

---

## exec

Generates `exec <absolute path><value>`. So you can define it with a relative path instead of the required absolute one.
It must be a string.

Example:

```text
exec: 'menu.cfg'
```

If the file where the property is defined is in `mainfolder/subfolder`,
it will result in:

```cfg
exec mainfolder/subfolder/menu.cfg
```

The relative path is automatically kept in a stack when defining folders, if you want to retrieve it, you can use `$PATH`.

---

## bind

Generates `bind <key> "<command>"`
It must be an array of objects.

Example:

```text
bind: [
    {
        key: '1'
        command: 'echo hello'
    }
]
```

Results in:

```cfg
bind 1 "echo hello"
```

A same bind can contain multiple properties, so you can bind to multiple commands:

```text
bind: [
    {
        key: '1'
        unbind: '2'
        command: [
            'echo hello'
            'exec /route/file.cfg'
        ]
    }
]
```

Results in:

```cfg
bind 1 "unbind 1;echo hello;exec /route/file.cfg"
```

---

## echo

Generates `cl_message_client_color <color>` followed by `echo <text>`
It must be an array of objects, containing a `color` and a `text` property. `color` must be a string, and `text` can be a string or an array of strings.

Example:

```text
echo: [
    {
        color: '$color1'
        text: 'Hello'
    }

    {
        color: '$color2'
        text: [
            'Line 1'
            'Line 2'
        ]
    }
]
```

Results in:

```cfg
cl_message_client_color 5635968
echo Hello

cl_message_client_color 5635418
echo Line 1
echo Line 2
```

---

# Variable resolution

Before writting any string into the final file, every string is passed through the variable resolution system where it will replace variables with their values. 
Every string can be replaced with a special `concat` property, which contains an array of strings. It must be written inside an object. This can be used to concatenate a string with a variable or other strings and put it in a single line. They dont have separation by default.

Example:

```text
command: [
    'line1'
    'line2'
    {concat: ['string1 ', '$variable', ' string2']}
]
```

Results in:

```cfg
line1
line2
string1 value string2
```
