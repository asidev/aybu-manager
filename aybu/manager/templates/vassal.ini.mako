[uwsgi]
instance_dir = ${instance.paths.dir}
chdir = %(instance_dir)
module = main
socket = ${instance.paths.socket}
master = true
processes = 1
threads = 1
idle = 120
lazy = true
cheap = true
reload-on-rss = 64
uid = ${os.user}
gid = ${os.group}
vacuum = true
no-orphan = true
single-interpreter = true
pyhome = ${instance.paths.virtualenv}
% for ctrl in instance.paths.cgroups:
cgroup = ${ctrl}
% endfor
logto = ${instance.paths.logs.vassal}
log-5xx = true

