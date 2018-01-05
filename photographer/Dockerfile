FROM python:3.6-slim

# Install OS level requirements
RUN apt-get update && apt-get install -y libpq-dev

# Add project specific content
WORKDIR /app
ADD . /app/

# Install project dependencies
RUN pip install -r requirements.txt

CMD python app.py
