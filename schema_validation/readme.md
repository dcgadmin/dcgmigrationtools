# Schema validation

Facilitate Heterogeneous Database schema validation. It Facilitate to validate Database objects migrated from Oracle to PostgreSQL.

## Features
Core Features is automating overall validation of all different database objects types like Function/Procedure/Triggers/Views/Table/Constraint and more.


## Dependencies

Schema validation uses many third party libraries which are mentioned below

- pandas  - used for data manipulation
- SQL alchemy - Adapter used for the database connection
- cx_Oracle - Adapter for oracle database connection
- psycopg2 - For interaction with PostgreSQL.
- matplotlib - For visualization and plot graph
- numpy - Used for chart data computing
- jinja2 - required for html template rendering


And of course schema validation itself is open source with a [public repository]
 on DataCloudGaze GitHub.

## Installation

Schema validation requires [Python](https://www.python.org/ftp/python/3.11.4/python-3.11.4-embed-amd64.zip) version 3.11.4 to run.

Install the dependencies  and start the server.

```sh
cd schema_validation
pip install -r requirements.txt (For windows 64-bit)
pip3 install -r requirements.txt (For macOS)
```



## Run

Schema validation allows you to put Oracle and PostgreSQL database credentials using command line argument

```sh
--ora-connection --pg-connection --ora-schema --pg-schema
```
The connection should be provided in below pattern
```
--ora-connection username:password@hostname:port/service_name
--pg-connection username:password@host:port/database_name
--ora-schema oracle schema name
--pg-schema postgresql schema name
```

You can see the details of every argument required by using following steps

```sh
cd schema_validation
python schema_validation.py --help
```


## Output

Once schema validation  if completed, you will find newly created reports within a directory (schema_validation_<schema_name>) as below
```sh
HTML report generated successfully.
Report Generated : schema_validation\schema_validation_dms_sample\oracle_pg_validation_<schema_name>.html
