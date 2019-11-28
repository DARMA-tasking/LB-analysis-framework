# Set environment variable
DOC_NAME=SAND2019-CALB
UNAME=$(uname)
PARAVIEW_VERSION=5.6.2
ARG_PATH=~/Documents/Git/arg

# Set ParaView environoment
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

# Clean up
rm -fR ${DOC_NAME} mutables.yml

# Run Generator to create pre-defined artifacts
#python ${ARG_PATH}/src/Applications/Generator.py

# Run Assembler to generate additional report artifacts and report
python ${ARG_PATH}/src/Applications/Assembler.py

# Move generated report to current directory
mv ${DOC_NAME}/${DOC_NAME}.pdf .
