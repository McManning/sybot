# Sybot

A Murmur server bot built for a handful of common tasks and service integrations.

## Features

### Flask API

Can report server metadata, as well as notify users of live stream changes (Nginx + RTMP module's `on_publish` handler)

### Commands

Includes an extendable interface for reacting to user input.

Commands include:

* **!pickone** - Select one item from a list at random. Eg: !pickone Gfro, Phantom, Mark
* **!#d#** - Roll dice. Eg: !2d6 will roll 2 six-sided dice

Also watches for common links to be posted and will report additional information about each link:

* YouTube links - Displays the video title the thumbnail
* Steam App links - Displays the app's title, description, reviews, and price
* Steam Workshop links - Displays the item's name, app name, and tags

## Installation

Sybot is built specifically to work with the composition of Docker images that make up the Sybolt infrastructure.

For docker-compose, configuration looks something like:

```yaml
sybot:
    image: mcmanning/sybot
    ports:
      - 5000:5000
    restart: on-failure
    depends_on:
      - murmur
    environment:
      - DEBUG=1
      - ICE_HOST=murmur
      - ICE_PORT=6502
      - ICE_SECRET=<string>
```

Sybot requires an instance of Murmur to be running first in order to connect with the Ice protocol.

## Current Issues

Running with `DEBUG=1` will cause the bot to run two separate Ice connections at once - as the Werkzeug backend is running multiple instances of the application to support hot reloading.
