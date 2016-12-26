from conan.packager import ConanMultiPackager
import copy

if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds(shared_option_name="libjpeg-turbo:shared", pure_c=True)

    builds = []
    for build in builder.builds:
        for version in [6, 7, 8]:
            build[1]["libjpeg-turbo:libjpeg_version"] = version
            builds.append(copy.deepcopy(build))
    builder.builds = builds
    builder.run()
