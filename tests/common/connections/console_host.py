from .base_console_conn import (
    CONSOLE_SSH,
    CONSOLE_SSH_CISCO_CONFIG,
    CONSOLE_SSH_MENU_PORTS,
    CONSOLE_TELNET,
    CONSOLE_SSH_DIGI_CONFIG,
    CONSOLE_SSH_SONIC_CONFIG
)
from .telnet_console_conn import TelnetConsoleConn
from .ssh_console_conn import SSHConsoleConn

ConsoleTypeMapper = {
    CONSOLE_TELNET: TelnetConsoleConn,
    CONSOLE_SSH: SSHConsoleConn,
    CONSOLE_SSH_MENU_PORTS: SSHConsoleConn,
    CONSOLE_SSH_DIGI_CONFIG: SSHConsoleConn,
    CONSOLE_SSH_SONIC_CONFIG: SSHConsoleConn,
    CONSOLE_SSH_CISCO_CONFIG: SSHConsoleConn,
}


def ConsoleHost(console_type,
                console_host,
                console_port,
                sonic_username,
                sonic_password,
                console_username=None,
                console_password=None,
                timeout_s=100):
    if console_type not in ConsoleTypeMapper:
        raise ValueError("console type {} is not supported yet".format(console_type))
    params = {
        "console_host": console_host,
        "console_port": console_port,
        "console_type": console_type,
        "sonic_username": sonic_username,
        "sonic_password": sonic_password,
        "console_username": console_username,
        "console_password": console_password,
        "timeout": timeout_s
    }
    return ConsoleTypeMapper[console_type](**params)
