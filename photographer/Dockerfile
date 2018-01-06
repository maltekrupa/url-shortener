FROM python:3.6-slim

# Install OS level requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq-dev \
  curl \
  bzip2 \
  libfreetype6 \
  libfontconfig

# Download and install phantomjs
RUN mkdir /tmp/phantomjs \
  && curl -L https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
         | tar -xj --strip-components=1 -C /tmp/phantomjs \
  && mv /tmp/phantomjs/bin/phantomjs /usr/local/bin \
  && rm -rf /tmp/phantomjs

# Add project specific content
WORKDIR /app
ADD . /app/

# Install project dependencies
RUN pip install -r requirements.txt

CMD bash
