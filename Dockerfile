FROM level12/shippable-python

VOLUME /opt/app/test_reports;
VOLUME /opt/app/artifacts;

WORKDIR /opt/app/src

CMD service postgresql start \
    && psql -U postgres -c 'create database testdb' \
    && pwd \
    && ls -la \
    && pip install --use-wheel --no-index --find-links=requirements/wheelhouse tox coveralls \
    && tox -e py27,py34,flake8,coveralls,circleci
