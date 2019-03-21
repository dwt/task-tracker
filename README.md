# Quickstart (using docker-compose)

`docker-compose up --build` or `make docker-build`

The app will be running at http://localhost/

# Slowstart (manual installation without docker)

## Requirements

- [Python](https://python.org) > 3.5
- [Yarn](https://yarnpkg.com/lang/en/docs/install)

## Development installation

Clone repository:

```
  git clone --recurse-submodules https://github.com/dwt/task-tracker
  cd task-tracker
```

Create virtual env:

```
  pyvenv .
  source bin/activate
```

Install [poetry](https://poetry.eustace.io/) python installer:

```
    bin/pip install -r requirements.txt
```

Install python and javascript dependencies

```
   poetry install
   yarn install
```




