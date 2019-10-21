#!/bin/sh

cd /app

sed -e "s/\${DB_HOST}/$DB_HOST/" \
    -e "s/\${DB_PORT}/$DB_PORT/" \
    -e "s/\${DB_USER}/$DB_USER/" \
    -i conf/gae_pgbouncer.ini

sed -e "s/\${DB_USER}/$DB_USER/" \
    -e "s/\${DB_PASSWORD}/$DB_PASSWORD/" \
    -i conf/gae_pgbouncer_users.txt

# Start the cloud-sql-proxy
./cloud_sql_proxy -dir=/cloudsql -instances=DB_HOST \
                  -credential_file=<PATH_TO_KEY_FILE> &

# Start the pgbouncer pool in local
pgbouncer -d -u pgbouncer `pwd`/conf/gae_pgbouncer.ini

# Start Crawler
python manage.py crawl $@
