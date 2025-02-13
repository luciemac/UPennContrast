# NimbusImage

[![Github Actions][github-actions-image]][github-actions-url]

## Project setup

```
npm install
```

## Development environment

```sh
git clone https://github.com/Kitware/UPennContrast.git
cd UPennContrast
npm install
docker-compose up -d
npm run serve
```

### Girder Defaults

By default, a admin user will be created with the name `admin` and the password `password`.  To use a different admin user, register a new user, log in as the `admin` user and make the new user an admin, then delete the original `admin` user.

A default assetstore is also created.

### Compiles and minifies for production

```
npm run build
```

### Lints and fixes files

```
npm run lint
```

### Customize configuration

See [Configuration Reference](https://cli.vuejs.org/config/).

[github-actions-image]: https://github.com/Kitware/UPennContrast/workflows/node/badge.svg
[github-actions-url]: https://github.com/Kitware/UPennContrast/actions
