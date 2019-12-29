FROM bgds/base-davinci:0.1

# DB connection information
ENV DB_USER davinci
ENV DB_PASSWORD davinci
ENV DB_NAME davinci

# CASSANDRA connection information
ENV CASSANDRA_DB_NAME davinci

RUN mkdir /davinci

ADD . /davinci/

RUN cd /davinci \
    && pip install . \
    && pip install django_caravaggio_rest_api[spatial] \
    && pip install -r requirements.txt || echo "ignore error" \
    && pip install -r requirements_tests.txt || echo "ignore error"

RUN mkdir -p /data/davinci_crawling/log

WORKDIR /davinci

VOLUME /davinci

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0:8000"]