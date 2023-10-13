FROM python:3.11.6-slim-bullseye as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/cguser/.local/bin:$PATH
ENV CG_APP_ENV="docker"

# Prepare environment
RUN mkdir /coingro \
  && apt-get update \
  && apt-get -y install sudo libatlas3-base curl sqlite3 libhdf5-serial-dev \
  && apt-get clean \
  && useradd -u 1000 -G sudo -U -m -s /bin/bash cguser \
  && chown cguser:cguser /coingro \
  # Allow sudoers
  && echo "cguser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /coingro

# Install dependencies
FROM base as python-deps
RUN  apt-get update \
  && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc libpq-dev python3-dev \
  && apt-get clean \
  && pip install --upgrade pip

# Install TA-lib
COPY build_helpers/* /tmp/
RUN cd /tmp && /tmp/install_ta-lib.sh && rm -r /tmp/*ta-lib*
ENV LD_LIBRARY_PATH /usr/local/lib

# Install dependencies
COPY --chown=cguser:cguser requirements.txt requirements-hyperopt.txt /coingro/
USER cguser
RUN  pip install --user --no-cache-dir numpy \
  && pip install --user --no-cache-dir -r requirements-hyperopt.txt

# Copy dependencies to runtime-image
FROM base as runtime-image
COPY --from=python-deps /usr/local/lib /usr/local/lib
ENV LD_LIBRARY_PATH /usr/local/lib

COPY --from=python-deps --chown=cguser:cguser /home/cguser/.local /home/cguser/.local

USER cguser
# Install and execute
COPY --chown=cguser:cguser . /coingro/

RUN pip install -e .[all] --user --no-cache-dir --no-build-isolation \
  && mkdir /coingro/user_data/ \
  && coingro create-userdir --userdir /coingro/user_data/

ENTRYPOINT ["coingro"]
# Default to trade mode
CMD [ "trade" ]
