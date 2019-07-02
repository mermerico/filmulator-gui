cmake -G"MSYS Makefiles" -DCMAKE_INSTALL_PREFIX="$MSYSTEM_PREFIX" -DCMAKE_BUILD_TYPE="Release" ../lrt
make -j4
make install
