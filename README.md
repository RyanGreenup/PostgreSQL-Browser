# PostgreSQL-Browser
A PostgreSQL Browser, similar to SQLiteBrowser with far less features (for now).

![](./screenshot_cli.png)
![](./screenshot.png)

## Installation

```python
# Append --force to update
pipx install "git+https://github.com/RyanGreenup/PostgreSQL-Browser"
```

## Usage

For testing purposes, consider the attached [docker-compose.yml](./docker-compose.yml) file to spin up a PostgreSQL instance.

```bash
cd $(mktemp -d)
git clone https://github.com/RyanGreenup/PostgreSQL-Browser"
cd PostgreSQL-Browser
docker-compose up -d
docker-compose logs -f
# C-c
curl https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_PostgreSql.sql > Chinook_PostgreSql.sql
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -f ~/Downloads/Chinook_PostgreSql.sql
```

```python
pg_browser --host localhost --password postgres --username postgres --port 5432
```

## Motivation

I wanted to browse my [linkwarden](https://github.com/linkwarden/linkwarden) database, and I didn't want to use the command line, now I can simply:

```python
alias lw_db="pg_browser  --host localhost --password ${LW_DB_PASS} --username postgres --port 37194"
lw_db
```

I was also hoping to move [my notetaking app](https://github.com/RyanGreenup/Draftsmith) to PostgreSQL, and I wanted a simple way to browse the database.





## Usage

### Importing Parquets

Import a directory of parquets into a PostgreSQL database. For the moment this requires a metadata.json file to describe types, in the future this will be inferred from the parquet files.

Here is an example of the JSON file:

<details closed><summary>

**Click to Unfold**
</summary>


```json
{
  "artist": [
    {
      "name": "artist_id",
      "type": "INTEGER"
    },
    {
      "name": "name",
      "type": "VARCHAR(120)"
    }
  ],
  "album": [
    {
      "name": "album_id",
      "type": "INTEGER"
    },
    {
      "name": "title",
      "type": "VARCHAR(160)"
    },
    {
      "name": "artist_id",
      "type": "INTEGER"
    }
  ],
  "employee": [
    {
      "name": "employee_id",
      "type": "INTEGER"
    },
    {
      "name": "last_name",
      "type": "VARCHAR(20)"
    },
    {
      "name": "first_name",
      "type": "VARCHAR(20)"
    },
    {
      "name": "title",
      "type": "VARCHAR(30)"
    },
    {
      "name": "reports_to",
      "type": "INTEGER"
    },
    {
      "name": "birth_date",
      "type": "TIMESTAMP"
    },
    {
      "name": "hire_date",
      "type": "TIMESTAMP"
    },
    {
      "name": "address",
      "type": "VARCHAR(70)"
    },
    {
      "name": "city",
      "type": "VARCHAR(40)"
    },
    {
      "name": "state",
      "type": "VARCHAR(40)"
    },
    {
      "name": "country",
      "type": "VARCHAR(40)"
    },
    {
      "name": "postal_code",
      "type": "VARCHAR(10)"
    },
    {
      "name": "phone",
      "type": "VARCHAR(24)"
    },
    {
      "name": "fax",
      "type": "VARCHAR(24)"
    },
    {
      "name": "email",
      "type": "VARCHAR(60)"
    }
  ],
  "customer": [
    {
      "name": "customer_id",
      "type": "INTEGER"
    },
    {
      "name": "first_name",
      "type": "VARCHAR(40)"
    },
    {
      "name": "last_name",
      "type": "VARCHAR(20)"
    },
    {
      "name": "company",
      "type": "VARCHAR(80)"
    },
    {
      "name": "address",
      "type": "VARCHAR(70)"
    },
    {
      "name": "city",
      "type": "VARCHAR(40)"
    },
    {
      "name": "state",
      "type": "VARCHAR(40)"
    },
    {
      "name": "country",
      "type": "VARCHAR(40)"
    },
    {
      "name": "postal_code",
      "type": "VARCHAR(10)"
    },
    {
      "name": "phone",
      "type": "VARCHAR(24)"
    },
    {
      "name": "fax",
      "type": "VARCHAR(24)"
    },
    {
      "name": "email",
      "type": "VARCHAR(60)"
    },
    {
      "name": "support_rep_id",
      "type": "INTEGER"
    }
  ],
  "invoice": [
    {
      "name": "invoice_id",
      "type": "INTEGER"
    },
    {
      "name": "customer_id",
      "type": "INTEGER"
    },
    {
      "name": "invoice_date",
      "type": "TIMESTAMP"
    },
    {
      "name": "billing_address",
      "type": "VARCHAR(70)"
    },
    {
      "name": "billing_city",
      "type": "VARCHAR(40)"
    },
    {
      "name": "billing_state",
      "type": "VARCHAR(40)"
    },
    {
      "name": "billing_country",
      "type": "VARCHAR(40)"
    },
    {
      "name": "billing_postal_code",
      "type": "VARCHAR(10)"
    },
    {
      "name": "total",
      "type": "NUMERIC(10, 2)"
    }
  ],
  "invoice_line": [
    {
      "name": "invoice_line_id",
      "type": "INTEGER"
    },
    {
      "name": "invoice_id",
      "type": "INTEGER"
    },
    {
      "name": "track_id",
      "type": "INTEGER"
    },
    {
      "name": "unit_price",
      "type": "NUMERIC(10, 2)"
    },
    {
      "name": "quantity",
      "type": "INTEGER"
    }
  ],
  "track": [
    {
      "name": "track_id",
      "type": "INTEGER"
    },
    {
      "name": "name",
      "type": "VARCHAR(200)"
    },
    {
      "name": "album_id",
      "type": "INTEGER"
    },
    {
      "name": "media_type_id",
      "type": "INTEGER"
    },
    {
      "name": "genre_id",
      "type": "INTEGER"
    },
    {
      "name": "composer",
      "type": "VARCHAR(220)"
    },
    {
      "name": "milliseconds",
      "type": "INTEGER"
    },
    {
      "name": "bytes",
      "type": "INTEGER"
    },
    {
      "name": "unit_price",
      "type": "NUMERIC(10, 2)"
    }
  ],
  "playlist": [
    {
      "name": "playlist_id",
      "type": "INTEGER"
    },
    {
      "name": "name",
      "type": "VARCHAR(120)"
    }
  ],
  "playlist_track": [
    {
      "name": "playlist_id",
      "type": "INTEGER"
    },
    {
      "name": "track_id",
      "type": "INTEGER"
    }
  ],
  "genre": [
    {
      "name": "genre_id",
      "type": "INTEGER"
    },
    {
      "name": "name",
      "type": "VARCHAR(120)"
    }
  ],
  "media_type": [
    {
      "name": "media_type_id",
      "type": "INTEGER"
    },
    {
      "name": "name",
      "type": "VARCHAR(120)"
    }
  ]
}
```
</details>
