FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends openssh-server \
 && rm -rf /var/lib/apt/lists/* && mkdir -p /run/sshd \
 && useradd -m -s /bin/bash admin && usermod -p '*' admin \
 && printf 'TrustedUserCAKeys /etc/ssh/trusted-user-ca.pem\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nLogLevel VERBOSE\n' \
    > /etc/ssh/sshd_config.d/acmefin.conf
CMD ["/usr/sbin/sshd", "-D", "-e"]
