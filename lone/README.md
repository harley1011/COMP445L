# COMP445L1

## Main request data

### GET

```
    {
        'type': 'GET',
        'url': 'www.google.com',
        'header':
            {
                'key1': 'value1',
                'key2': 'value2'
            },
        'verbose': True
    }
```

### POST

```
    {
        'type': 'POST',
        'url': 'www.google.com',
        'header':
            {
                'key1': 'value1',
                'key2': 'value2'
            },
        'verbose': True,
        'data': {
            'type': 'inline',  # [inline] or [file]
            'value': 'test'
        }
    }
```