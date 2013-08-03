#!/bin/sh

if [ -e ~/.config/inkscape/extensions/ ]; then
    EXTDIR=~/.config/inkscape/extensions/
else
    EXTDIR=~/.inkscape/extensions/
fi

cp *.inx *.py $EXTDIR

macinkscape=/Applications/Inkscape.app/Contents/MacOS/Inkscape

if [ -e $macinkscape ] ; then
    $macinkscape
else
    inkscape $*
fi
