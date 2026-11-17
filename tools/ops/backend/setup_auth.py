"""Create initial local credentials without overwriting existing files.

한글: 기존 파일을 덮어쓰지 않고 초기 로컬 로그인 정보를 생성한다.
"""
import json
import os
import secrets
import sys
import getpass

from access_control import ACCOUNTS, password_hash


def main():
    """Create viewer/operator accounts and a private one-time credential file.

    한글: 조회자·운영자 계정과 사용자 전용 초기 비밀번호 파일을 만든다.
    """
    if len(sys.argv) == 3 and sys.argv[1] == 'password' and sys.argv[2] in ('viewer', 'operator'):
        role = sys.argv[2]
        password = getpass.getpass('새 비밀번호: ')
        if len(password) < 12 or password != getpass.getpass('새 비밀번호 확인: '):
            raise ValueError('비밀번호는 12자 이상이어야 하며 확인값과 같아야 합니다')
        accounts = json.loads(ACCOUNTS.read_text())
        salt = secrets.token_hex(16)
        accounts[role] = {'role': role, 'salt': salt, 'hash': password_hash(password, salt)}
        temp = ACCOUNTS.with_name('accounts.json.new')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as output:
            json.dump(accounts, output)
        os.replace(temp, ACCOUNTS)
        print('Password updated; restart the dashboard to revoke existing sessions')
        return
    if len(sys.argv) != 1:
        raise ValueError('usage: setup_auth.py [password viewer|operator]')
    directory = ACCOUNTS.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    passwords = {role: secrets.token_urlsafe(18) for role in ('viewer', 'operator')}
    accounts = {}
    for role, password in passwords.items():
        salt = secrets.token_hex(16)
        accounts[role] = {'role': role, 'salt': salt, 'hash': password_hash(password, salt)}
    credentials = directory / 'initial-passwords.txt'
    if credentials.exists() or ACCOUNTS.exists():
        raise FileExistsError('authentication files already exist; no files were changed')
    for path, content in ((credentials, '\n'.join(f'{k}: {v}' for k, v in passwords.items()) + '\n'),
                          (ACCOUNTS, json.dumps(accounts))):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as output:
            output.write(content)
    print(f'Credentials saved to {credentials}')


if __name__ == '__main__':
    main()
