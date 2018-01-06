FROM python:3.6-slim

# Install OS level requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq-dev

# Add project specific content
WORKDIR /app
ADD . /app/

# Install project dependencies
RUN pip install -r requirements.txt

CMD gunicorn -b :5000 --workers=2 app:app
