FROM level12/python-test-multi

# install additional dependencies
RUN apt-get install -y \
    libxslt1.1 \
    libxml2
