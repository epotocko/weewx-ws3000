# installer for ws3000 driver

from setup import ExtensionInstaller

def loader():
    return WS3000Installer()

class WS3000Installer(ExtensionInstaller):
    def __init__(self):
        super(WS3000Installer, self).__init__(
            version="0.1",
            name='ws3000',
            description='Collect data from WS-3000 temperature/humidity sensors',
            author="Unknown",
            files=[('bin/user', ['bin/user/hp3000.py', 'bin/user/ws3000Extensions.py'])])
