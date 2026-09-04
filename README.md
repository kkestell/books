# Books

A private Rails application for importing and browsing ebook libraries.

## Run locally with demo data

Run the setup script from the repository root:

```sh
bin/setup
```

It installs missing gems, prepares the development database, adds a dozen
downloadable demo books to Kyle's library, and starts the app. Open
<http://localhost:3000/libraries/kyle>.

The seeds are idempotent, so they are safe to run again without duplicating the
demo books:

```sh
bin/rails db:seed
bin/dev
```

Use `bin/setup --reset` when you want to rebuild the local database from
scratch. Demo books are created only in development; production seeds create
the empty Kyle and Liz libraries.

## Test

```sh
bin/rails test
bin/rails test:system
```
