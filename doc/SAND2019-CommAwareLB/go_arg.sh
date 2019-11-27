# Set up ParaView Python environment
UNAME=$(uname)
PARAVIEW_VERSION=5.6.2

if [ "$UNAME" = "Linux" ] ; then
        if [ -z ${PARAVIEW_PATH} ] ; then
                export PARAVIEW_PATH="/opt/paraview-${PARAVIEW_VERSION}"
        fi
        export LD_LIBRARY_PATH="${PARAVIEW_PATH}/lib/"
        export PYTHONPATH="${PYTHONPATH}:${PARAVIEW_PATH}/lib/python2.7/site-packages:${PARAVIEW_PATH}/lib/python2.7/site-packages/vtkmodules"
elif [ "$UNAME" = "Darwin" ] ; then
        #if [ -z ${PARAVIEW_PATH} ] ; then
                export PARAVIEW_PATH="/Applications/ParaView-${PARAVIEW_VERSION}.app"
        #fi
        export DYLD_FALLBACK_LIBRARY_PATH="${PARAVIEW_PATH}/Contents/Libraries"
        export PYTHONPATH="${PYTHONPATH}:${PARAVIEW_PATH}/Contents/Python"
        echo $DYLD_FALLBACK_LIBRARY_PATH
elif [[ "$UNAME" == CYGWIN* || "$UNAME" == MINGW* ]] ; then
        if [ "$ProgramW6432" != "" ] ; then
                export PROG="$PROGRAMFILES"
        else
                export PROG="$ProgramFiles(x86)"
        fi
        if [ -z "$PARAVIEW_PATH" ] ; then
                export PARAVIEW_PATH="$PROG/ParaView-${PARAVIEW_VERSION}-Windows-msvc2015-64bit/bin/Lib/site-packages;$PROG/ParaView-${PARAVIEW_VERSION}-Windows-msvc2015-64bit/bin/Lib/site-packages/paraview;$PROG/ParaView-${PARAVIEW_VERSION}-Windows-msvc2015-64bit/bin/Lib/site-packages/vtkmodules"
        fi
        export PYTHONPATH="$HOMEDRIVE/Python27/Lib/site-packages/;${PARAVIEW_PATH}"
fi

# Report on ParaView and Python environment variables for debugging purposes
echo PARAVIEW_PATH=${PARAVIEW_PATH}
echo PYTHONPATH=${PYTHONPATH}
python -c 'import sys; print("Encoding is {}".format("UCS4" if sys.maxunicode > 65536 else "UCS2"))'
python -c 'import paraview.vtk as vtk; print("Python VTK module is {}".format(vtk))'

# Clean-up
rm -fR @NAME@.@EXT@ mutables.yml @NAME@ artifact


# Substitute report name
sed -e 's/@NAME@/Report-crush/g' -i'' test.tmp 2> /dev/null ||
 # execute sed -i '' if an error occured (macOS workaround)
(sed -e 's/@NAME@/Report-crush/g' -i '' test.tmp)

# Substitute report extension
sed -e 's/@EXT@/pdf/g' -i'' test.tmp 2> /dev/null ||
 # execute sed -i '' if an error occured (macOS workaround)
(sed -e 's/@EXT@/pdf/g' -i '' test.tmp)

# Execute runner
sh test.tmp

# Get runner exitcode
exitcode=$?

# Clean up runner
rm -f test.tmp

exit $exitcode
