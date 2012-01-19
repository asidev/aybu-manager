[uwsgi]
instance_dir = ${instance.paths.dir}
chdir = %(instance_dir)
module = main
#socket = ${instance.paths.socket}
socket = :0
subscribe-to = ${instance.environment.uwsgi_config.subscription_server.address}:${instance.environment.uwsgi_config.subscription_server.port}:@${instance.paths.dir}/domains.txt
static-map = /static=${instance.paths.instance_dir}/static
% for theme in instance.themes_chain:
static-map = /static=${instance.environment.paths.themes}/${theme.name}/static
% endfor
master = true
post-buffering = 1024
processes = 1
threads = 1
idle = 120
lazy = true
cheap = true
reload-on-rss = 64
uid = ${instance.environment.os_config.user}
gid = ${instance.environment.os_config.group}
vacuum = true
no-orphan = true
single-interpreter = true
pyhome = ${instance.paths.virtualenv}
% for ctrl in instance.paths.cgroups:
cgroup = ${ctrl}
% endfor
logto = ${instance.paths.logs.vassal}
log-5xx = true

