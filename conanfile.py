from conans import ConanFile, CMake, tools, ConfigureEnvironment, errors
import os


class LibJpegTurboConan(ConanFile):
    name = "libjpeg-turbo"
    version = "1.5.1"
    sha1 = "ebb3f9e94044c77831a3e8c809c7ea7506944622"
    license = "https://github.com/libjpeg-turbo/libjpeg-turbo/blob/%s/LICENSE.md" % version
    url = "https://github.com/Mikayex/conan-libjpeg-turbo.git"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "libjpeg_version": [6, 7, 8], "simd": [True, False],
               "with_12bit": [True, False], "with_turbojpeg": [True, False]}
    default_options = "shared=True", "libjpeg_version=6", "simd=True", "with_12bit=False", "with_turbojpeg=True"
    generators = "cmake", "txt"
    build_policy = "missing"

    def configure(self):
        del self.settings.compiler.libcxx  # Pure C project
        if self.options.with_12bit:
            if self.options.simd or self.options.with_turbojpeg:
                self.output.warn("'with_12bit' option implies 'simd=False' and 'with_turbojpeg=False'")
            self.options.simd = False
            self.options.with_turbojpeg = False

    def requirements(self):
        if (self.settings.arch == "x86" or self.settings.arch == "x86_64") and self.options.simd:
            self.requires("nasm/[>=2.7,<2.11.8||>2.11.8]@Mikayex/stable", private=True)

    @property
    def nasm_command(self):
        for dir in self.deps_cpp_info["nasm"].bin_paths:
            nasm = os.path.join(dir, "nasm.exe" if self.settings.os == "Windows" else "nasm")
            if os.path.exists(nasm):
                return nasm

    def source(self):
        tools.download("http://downloads.sourceforge.net/project/libjpeg-turbo/%s/libjpeg-turbo-%s.tar.gz"
                       % (self.version, self.version), "libjpeg-turbo.tar.gz")
        tools.check_sha1("libjpeg-turbo.tar.gz", self.sha1)
        tools.untargz("libjpeg-turbo.tar.gz")
        os.unlink("libjpeg-turbo.tar.gz")
        if self.settings.os == "Windows":
            tools.replace_in_file("libjpeg-turbo-%s/CMakeLists.txt" % self.version, "project(libjpeg-turbo C)",
                                  """project(libjpeg-turbo C)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()""")
            tools.replace_in_file("libjpeg-turbo-%s/CMakeLists.txt" % self.version,
                                  'string(REGEX REPLACE "/MD" "/MT" ${var} "${${var}}")', '')

        if self.settings.os == "Macos":
            tools.replace_in_file("libjpeg-turbo-%s/configure" % self.version, '-install_name \$rpath/\$soname',
                                  '-install_name \$soname')

    def build(self):
        if self.settings.os == "Windows":
            cmake = CMake(self.settings)
            cmake_flags = [
                "-DENABLE_SHARED=ON" if self.options.shared else "-DENABLE_SHARED=OFF",
                "-DENABLE_STATIC=OFF" if self.options.shared else "-DENABLE_STATIC=ON",
                "-DWITH_SIMD=ON" if self.options.simd else "-DWITH_SIMD=OFF",
                "-DWITH_12BIT=ON" if self.options.with_12bit else "-DWITH_12BIT=OFF",
                "-DWITH_TURBOJPEG=ON" if self.options.with_turbojpeg else "-DWITH_TURBOJPEG=OFF"
            ]
            if self.options.libjpeg_version != 6:
                cmake_flags.append("-DWITH_JPEG%s=ON" % self.options.libjpeg_version)
            if (self.settings.arch == "x86" or self.settings.arch == "x86_64") and self.options.simd:
                cmake_flags.append("-DNASM=\"%s\"" % self.nasm_command)

            self.run("cmake libjpeg-turbo-%s %s %s" % (self.version, ' '.join(cmake_flags), cmake.command_line))
            self.run("cmake --build . %s" % cmake.build_config)
        else:
            env = ConfigureEnvironment(self).command_line

            build_type_flags = ""
            if self.settings.build_type == "Release":
                build_type_flags = "-O3"
            elif self.settings.build_type == "Debug":
                build_type_flags = "-g"
            env = env.replace('CFLAGS="', 'CFLAGS="%s ' % build_type_flags)

            config_flags = [
                "--enable-shared" if self.options.shared else "--disable-shared",
                "--disable-static" if self.options.shared else "--enable-static",
                "--with-simd" if self.options.simd else "--without-simd",
                "--with-12bit" if self.options.with_12bit else "--without-12bit",
                "--with-turbojpeg" if self.options.with_turbojpeg else "--without-turbojpeg"
            ]

            if self.options.libjpeg_version != 6:
                config_flags.append("--with-jpeg%s" % self.options.libjpeg_version)

            if (self.settings.arch == "x86" or self.settings.arch == "x86_64") and self.options.simd:
                env += " NASM=\"%s\"" % self.nasm_command

                if self.settings.arch == "x86":
                    if self.settings.os == "Linux":
                        config_flags.append("--host i686-pc-linux-gnu")
                    elif self.settings.os == "Macos":
                        config_flags.append("--host i686-apple-darwin")
                    else:
                        errors.ConanException("Unknown x86 platform, please report it at %s" % self.url)

            self.run("%s ./libjpeg-turbo-%s/configure %s" % (env, self.version, " ".join(config_flags)))
            self.run("%s make" % env)

    def package(self):
        src = "./libjpeg-turbo-%s" % self.version

        # Includes
        self.copy("jconfig.h", dst="include", src=".", keep_path=False)
        self.copy("jerror.h", dst="include", src=src, keep_path=False)
        self.copy("jmorecfg.h", dst="include", src=src, keep_path=False)
        self.copy("jpeglib.h", dst="include", src=src, keep_path=False)

        if self.options.with_turbojpeg:
            self.copy("turbojpeg.h", dst="include", src=src, keep_path=False)

        # Libs
        self.copy("*.dll", dst="bin", src=".", keep_path=False)
        self.copy("*jpeg*.lib", dst="lib", src=".", keep_path=False)
        self.copy("*jpeg*.a", dst="lib", src=".", keep_path=False)
        self.copy("*jpeg*.so", dst="lib", src=".", keep_path=False, links=True)
        self.copy("*jpeg*.so.*", dst="lib", src=".", keep_path=False, links=True)
        self.copy("*jpeg*.dylib*", dst="lib", src=".", keep_path=False, links=True)

        # Executables
        ext = ".exe" if self.settings.os == "Windows" else ""
        self.copy("*cjpeg%s" % ext, dst="bin", src=".", keep_path=False)
        self.copy("*djpeg%s" % ext, dst="bin", src=".", keep_path=False)
        self.copy("*jpegtran%s" % ext, dst="bin", src=".", keep_path=False)
        self.copy("*rdjpgcom%s" % ext, dst="bin", src=".", keep_path=False)
        self.copy("*wrjpgcom%s" % ext, dst="bin", src=".", keep_path=False)

    def package_info(self):
        self.cpp_info.bindirs = ["bin"]
        self.cpp_info.libs = ["jpeg"]
        if self.options.with_turbojpeg:
            self.cpp_info.libs.append("turbojpeg")
