#!/bin/sh
# Install the small game set on first boot; the marker on /data makes it once.
if [ ! -d /data ]; then
    exit 0
fi
if [ -f /data/games/.installed-core ]; then
    exit 0
fi
sh /system/bin/install-games.sh core
