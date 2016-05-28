#!/bin/sh

if [ ! -x .tox/node/node_modules/bower/bin/bower ]; then
    npm install --prefix .tox/node bower 
fi
.tox/node/node_modules/bower/bin/bower install
pip install $*
