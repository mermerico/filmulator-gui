cmake -G"MSYS Makefiles" -DCMAKE_BUILD_TYPE="$BUILD_TYPE"-DCMAKE_INSTALL_PREFIX=$INSTALLDIR ../filmulator-gui >output.log 2>err.log
make -j4
make install
