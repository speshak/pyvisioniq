FROM python:3.12-alpine

WORKDIR /app
COPY . .

# Set some reasonable defaults for env vars
ENV BLUELINKUPDATE=True
ENV BLUELINKPIN=""

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001
ENTRYPOINT ["python", "pyvisioniq.py"]
