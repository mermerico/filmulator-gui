vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO mermerico/librtprocess
    REF 2ea99118c38a62ddbd0695b4af8f202492fa983e
    SHA512 a07e474400bdb54bfb33c09ecdbf40188eae514d9ec89afb3813eac366143c4d5d7fcb7d450c33f1e1916f9bb937ef53f46e3458e10e9e7a3c989b74d0725d2c
    HEAD_REF vcpkg-integration
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -DBUILD_SHARED_LIBS=OFF
)

vcpkg_cmake_install()
vcpkg_cmake_config_fixup(PACKAGE_NAME rtprocess CONFIG_PATH lib/cmake/rtprocess)

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/share")

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/LICENSE.txt")
