# Schism

A flat registration system written in Python with Flask.

## Deployment

We assume that the following commands are going to be run on a fresh
installation of [Debian GNU/Linux][].

### On your local machine

Run the following:

```shell
$ ssh-keygen -t ed25519
$ ssh-copy-id -i ~/.ssh/your_public_key.pub user@server
```
replacing `user` by your actual username at the machine `server`.

### On your server

Install some packages:

```shell
$ sudo apt install ufw                           # an interface used to configure the firewall 
$ sudo apt install python3-venv python3-pip      # for Python3 virtual environments
$ sudo apt install mariadb-server mariadb-client # the database server
$ sudo apt install nginx                         # the webpages server
$ sudo apt install certbot                       # to certify the server with Let's Encrypt
$ sudo apt install git                           # to control the version of our code
$ sudo apt install make supervisor               # for our convenience
```

Enable the firewall:

```shell
$ sudo ufw default deny
$ sudo ufw allow ssh
$ sudo ufw allow "Nginx Full"
$ sudo ufw enable
$ sudo ufw status numbered
```

and disable:

  - SSH login as root: `PermitRootLogin no`
  - Password authentication: `PasswordAuthentication no`

by adding the above directives to the right of the colons to the file
`/etc/ssh/sshd_config`

```shell
$ sudo vi /etc/ssh/sshd_config
```

```shell
$ git clone https://github.com/mpbsd/schism
$ cd ~/schism
$ make ready
```

[Debian GNU/Linux]: https://debian.org
