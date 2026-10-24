[app]
title = Fazenda RPG
package.name = fazendarpg
package.domain = org.fazenda
source.dir = .
source.include_exts = py,png,json
source.exclude_dirs = tests,tools,runtime,pylibs,web_build,dist,build,.github,bin
version = 1.0
requirements = python3,pygame
orientation = landscape
fullscreen = 1
icon.filename = %(source.dir)s/assets/icon.png
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
