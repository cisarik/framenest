#!/usr/bin/env fish
# Strict noninteractive SSH gate for bounded NUC operator commands.

set -e APPIMAGE APPDIR ARGV0 LD_LIBRARY_PATH LD_PRELOAD

set -l trusted_path /usr/sbin:/usr/bin:/sbin:/bin

function _gate_usage
    echo "Usage: framenest_nuc_worker_gate.fish --target <name> --user <user> --identity <file> --command <bounded-command>" >&2
end

function _is_absolute_executable
    set -l candidate $argv[1]
    if not string match -q '/*' -- $candidate
        return 1
    end
    if string match -q '*..*' -- $candidate
        return 1
    end
    if not test -f $candidate -a -x $candidate
        return 1
    end
    return 0
end

function _trusted_lookup
    set -l name $argv[1]
    begin
        set -l PATH /usr/sbin /usr/bin /sbin /bin
        command -v $name
    end
end

function _resolve_tool
    set -l name $argv[1]
    set -l override ""
    if test (count $argv) -ge 2
        set override $argv[2]
    end
    if test "$FRAMENEST_NETWORK_TEST_HOOKS" = 1
        if test -n "$override"
            if _is_absolute_executable $override
                echo $override
                return 0
            end
            echo "Test hook tool path is not a trusted absolute executable." >&2
            return 1
        end
        echo "Required tool '$name' is not provided through the test hook." >&2
        return 1
    end
    set -l found (_trusted_lookup $name)
    or true
    if test -z "$found"
        echo "Required tool '$name' was not found in the trusted executable search path." >&2
        return 1
    end
    if not _is_absolute_executable $found
        echo "Required tool '$name' was not found in the trusted executable search path." >&2
        return 1
    end
    echo $found
end

function _optional_gpgconf
    if test "$FRAMENEST_NETWORK_TEST_HOOKS" = 1
        if test -n "$FRAMENEST_NETWORK_TEST_GPGCONF"
            if _is_absolute_executable $FRAMENEST_NETWORK_TEST_GPGCONF
                echo $FRAMENEST_NETWORK_TEST_GPGCONF
            end
        end
        return 0
    end
    set -l found (_trusted_lookup gpgconf)
    or true
    if test -n "$found"; and _is_absolute_executable $found
        echo $found
    end
end

set -l target $FRAMENEST_NUC_SSH_TARGET
set -l remote_user $FRAMENEST_NUC_SSH_USER
set -l identity $FRAMENEST_NUC_SSH_IDENTITY
set -l remote_command $FRAMENEST_NUC_SSH_COMMAND

while test (count $argv) -gt 0
    switch $argv[1]
        case -h --help
            _gate_usage
            exit 0
        case --target
            if test (count $argv) -lt 2
                echo "Missing value for --target." >&2
                exit 2
            end
            set target $argv[2]
            set argv $argv[3..]
        case --user
            if test (count $argv) -lt 2
                echo "Missing value for --user." >&2
                exit 2
            end
            set remote_user $argv[2]
            set argv $argv[3..]
        case --identity
            if test (count $argv) -lt 2
                echo "Missing value for --identity." >&2
                exit 2
            end
            set identity $argv[2]
            set argv $argv[3..]
        case --command
            if test (count $argv) -lt 2
                echo "Missing value for --command." >&2
                exit 2
            end
            set remote_command $argv[2]
            set argv $argv[3..]
        case '*'
            echo "Unknown or extra operand: $argv[1]" >&2
            _gate_usage
            exit 2
    end
end

if test -z "$target"
    echo "Missing remote target." >&2
    _gate_usage
    exit 2
end
if test -z "$remote_user"
    echo "Missing remote user." >&2
    _gate_usage
    exit 2
end
if test -z "$identity"
    echo "Missing identity file." >&2
    _gate_usage
    exit 2
end
if test -z "$remote_command"
    echo "Missing bounded remote command." >&2
    _gate_usage
    exit 2
end

if string match -qr '[[:space:]]' -- $target
    echo "Remote target must not contain whitespace." >&2
    exit 2
end
if string match -q -- '-*' $target
    echo "Remote target must not be option-like." >&2
    exit 2
end
if string match -q '*@*' -- $target
    echo "Remote target must not include a user prefix." >&2
    exit 2
end
if not string match -qr '^[A-Za-z0-9][A-Za-z0-9.-]*$' -- $target
    echo "Remote target is not a valid hostname." >&2
    exit 2
end

if string match -qr '[[:space:]]' -- $remote_user
    echo "Remote user must not contain whitespace." >&2
    exit 2
end
if string match -q -- '-*' $remote_user
    echo "Remote user must not be option-like." >&2
    exit 2
end
if not string match -qr '^[A-Za-z_][A-Za-z0-9_-]*$' -- $remote_user
    echo "Remote user is not a valid login name." >&2
    exit 2
end

if string match -qr '[[:space:]]' -- $identity
    echo "Identity file path must not contain whitespace." >&2
    exit 2
end
if string match -q -- '-*' $identity
    echo "Identity file path must not be option-like." >&2
    exit 2
end
if not test -f $identity
    echo "Identity file is missing or not a regular file." >&2
    exit 2
end

if string match -q -- '-*' $remote_command
    echo "Remote command must not be option-like." >&2
    exit 2
end
if string match -qr '[\n;|&$`<>(){}]' -- $remote_command
    echo "Remote command contains unsupported shell metacharacters." >&2
    exit 2
end

set -l ssh_bin
set ssh_bin (_resolve_tool ssh $FRAMENEST_NETWORK_TEST_SSH)
or exit $status

set -l gpgconf_bin
set gpgconf_bin (_optional_gpgconf)
if test -n "$gpgconf_bin"
    set -l agent_sock
    set agent_sock (env -u APPIMAGE -u APPDIR -u ARGV0 -u LD_LIBRARY_PATH -u LD_PRELOAD PATH=$trusted_path $gpgconf_bin --list-dirs agent-ssh-socket 2>/dev/null)
    if test $status -eq 0; and test -n "$agent_sock"; and test -S "$agent_sock"
        set -gx SSH_AUTH_SOCK $agent_sock
    end
end

set -l ssh_args
set -a ssh_args -o BatchMode=yes
set -a ssh_args -o RequestTTY=no
set -a ssh_args -o StrictHostKeyChecking=yes
set -a ssh_args -o IdentitiesOnly=yes
set -a ssh_args -o ForwardAgent=no
set -a ssh_args -o ClearAllForwardings=yes
set -a ssh_args -o ConnectTimeout=10
set -a ssh_args -o ServerAliveInterval=15
set -a ssh_args -o ServerAliveCountMax=2
set -a ssh_args -i $identity
set -a ssh_args $remote_user@$target
set -a ssh_args $remote_command

env -u APPIMAGE -u APPDIR -u ARGV0 -u LD_LIBRARY_PATH -u LD_PRELOAD \
    PATH=$trusted_path \
    $ssh_bin $ssh_args
exit $status
