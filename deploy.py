import paramiko
import sys, os
from subprocess import PIPE, Popen

# Need gpg keys
# Need ssh keys

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
        print (f'RETURN:\n\t{out}')
        self._ssh.close ()
        return out


def run (cmd:str):
    stdout = ''
    stderr = ''
    status = 1

    with Popen(cmd.split (' ')) as proc:
        stdout, stderr = proc.communicate ()
        status = proc.returncode

    if status != 0:
        print(f'{stdout}\n{stderr}')
        sys.exit(status)
    
    return stdout

def reborn_spec (old_spec_path:str, template_spec_path:str, new_spec_path:str):
    # epoch:str = ''
    version:str = ''
    release:str = ''
    changelog:list[str] = []

    with open (old_spec_path, 'r') as f:
        for line in f.readlines ():
            if changelog:
                changelog.append (line)
                continue

            if line.startswith ('Version:'):
                version = line.lstrip ('Version:').strip ()
            elif line.startswith ('Release:'):
                release = line.lstrip ('Release:').strip ()
            # elif line.startswith ('Epoch:'):
            #     epoch = line.lstrip ('Epoch:').strip ()
            elif '%changelog' in line:
                changelog.append (line.strip ())

    with open (new_spec_path, 'w') as new_f:
        with open (template_spec_path, 'r') as tmplt_f:
            for line in tmplt_f.readlines ():
                if line.startswith ('Version:'):
                    new_f.write ([f'Version: {version}\n'])
                elif line.startswith ('Release:'):
                    new_f.write ([f'Release: {release}\n'])
                else:
                    new_f.write (line)
            
        for chlog in changelog:
            new_f.write (f'{chlog}\n')

    os.remove (old_spec_path)
    os.remove (template_spec_path)
    os.rename (new_spec_path, old_spec_path)


if __name__ == '__main__':
    if len (sys.argv) < 7:
        print (f"Not enough args. Got {len (sys.argv) - 1}, expected: 7")
        print ("Need:")
        print ("password task_num repo_name new_version target_commit ready_to_sisyphus(bool)")
        sys.exit (1)

    password = sys.argv[1]
    task_num = sys.argv[2]
    repo_name = sys.argv[3]
    new_version = sys.argv[4]
    target_commit = sys.argv[5]
    ready_to_sisyphus = bool (sys.argv[6])

    run (f'git checkout upstream/main build-aux/sisyphus/{repo_name}.spec')
    run (f'git reset build-aux/sisyphus/{repo_name}.spec')
    reborn_spec (f'{repo_name}.spec', f'build-aux/sisyphus/{repo_name}.spec', f'{repo_name}-new.spec')
    run (f'git add {repo_name}.spec')
    if (run ('git status --porcelain')):
        run (f'git commit -m "update spec"')
        run ('git push')

    run (f'gear-uupdate --upstream-version {new_version} --commit {target_commit} --ch " - {new_version}"')
    run ('gear-commit')
    run ('git push')
    run ('gear-create-tag')

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
    gyle.execute (f'task run {"--commit " if ready_to_sisyphus is True else ""}{task_num}')
