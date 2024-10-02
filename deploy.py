import paramiko
import sys, os
from subprocess import PIPE, Popen


class SshWrapper():
    
    _ssh = paramiko.SSHClient()
    
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
    def execute (self, command):
        print (f'EXEC:\n\t{command}')
        self._ssh.connect(self.host, username=self.username, port='222', password=self.password)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        out = stdout.read().decode()
        print (f"RETURN:\n\t{out}")
        self._ssh.close ()
        return out


password = sys.argv[1]
task_num = sys.argv[2]
repo_name = sys.argv[3]
new_version = sys.argv[4]
to_sithyfus = bool (sys.argv[5])

gyle = SshWrapper('gyle.altlinux.org', 'alt_rirusha', password)

with Popen (['git', 'clone', f'gitery:packages/{repo_name}.git'], stdout=sys.stdout, stderr=sys.stderr) as proc:
    proc.communicate ()
with Popen (['cd', repo_name], stdout=sys.stdout, stderr=sys.stderr) as proc:
    proc.communicate ()
# move new spec
# commit
# gear uupdate by commit
# gear-commit fix changelog

output = gyle.execute (f'task show {task_num}')
outlines = output.split('\n')
if "locked=yes" in outlines[0]:
    print ("Task is locked")
    sys.exit(0)
last_sub = outlines[-2].split(":")[0]

gyle.execute (f'task delsub {task_num} {last_sub}')
gyle.execute (f'task add {task_num} repo {repo_name} {new_version}-alt1')
gyle.execute (f'task run {"--commit " if to_sithyfus is True else ""}{task_num}')
