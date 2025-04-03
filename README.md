Hello!

Thank you for the nice assessment test, it was fun! Before we continue I wanted to note a couple things.

1. Please see `NOTES.md`, it explains any design decisions or things
   I encountered during this test.
2. All other files, including this one, I will be "in character".
   Please read this as though it were a real git repository.
3. If I need to "break character", I will note it with a "XXX:" prefix.

That's all for now!


# metview
`metview` lets you easily view, search, filter, and browse great Works of Art from
[The Metropolitan Museum Of Art](The Metropolitan Museum Of Art)!


## How To Use
TODO: Fill this out later


### How To Use - Manually
```sh
python -m metview
```


### Environment Variables
Simple customizations for the `metview` CLI.

| Name  | Default | Description |
|------|-------|------------|
| MET_MUSEUM_API_DOMAIN | "https://collectionapi.metmuseum.org" | The URL to look within for API calls. |

> [!IMPORTANT]
> If any environment variable has a CLI argument, the argument will be given priority!


## Developing
#### How To Lint / CI Check
```sh
tox -e check-mypy
tox -e check-pylint
tox -e check-pydocstyle
tox -e check-isort
tox -e check-black
```

### How To Test
```sh
tox -e python-{version}
# e.g.
tox -e python-3.12
tox -e python-3.11
tox -e python-3.10
tox -e python-3.9
```
