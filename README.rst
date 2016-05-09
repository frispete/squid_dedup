squid_dedup
===========

squid_dedup is a squid proxy helper, helping to reduce cache misses when
identical content is accessed using different URLs (aka CDNs).

This helper implements the squid StoreID protocol, as found in squid 3
onwards. URL patterns, specified in config files, are rewritten to a presumably
unique internal address. Further accesses, modified in the same way, map to
already stored objects, even if using different URLs.

Global configuration options are specified in the primary config file, which
must exist. A template can be created with the --extract command line switch in
the current directory.

CDN match/replacement parameter are specified in additional config files.


Installation
------------

::

    $ python3 setup.py install

Create directory for custom config files::

    $ mkdir /etc/squid/dedup

Create primary config file template /etc/squid/squid_dedup.conf::

    $ cd /etc/squid
    $ squid_dedup -X

openSUSE CDN::

    $ gen_openSUSE_dedups

creates /etc/squid/dedup/opensuse.conf.


Activation
----------

Add similar values to /etc/squid/squid.conf::

    store_id_program /usr/bin/squid_dedup
    store_id_children 20 startup=10 idle=5 concurrency=0

    acl getmethod method GET
    store_id_access deny !getmethod
    store_id_access allow all

That's it.


Configuration
-------------

The primary configuration is located in /etc/squid/squid_dedup.conf,
and defines the general behaviour.

Additional config files should be stored in /etc/squid/dedup, e.g.::

    [sourceforge]
    match: http:\/\/[a-zA-Z0-9\-\_\.]+\.dl\.sourceforge\.net\/(.*)
    replace: http://dl.sourceforge.net.%(intdomain)s/\1
    fetch: false

Here, any URL pointing to a sub domain of dl.sourceforge.net, is mapped to
dl.sourceforge.net.%(intdomain)s, where %(intdomain)s is replaced according
to the value of intdomain in /etc/squid/squid_dedup.conf.

match is a list of regular expressions matching URLs, separated by newlines,
with all subsequent URLs indented.

replace is a single replacement value.

fetch is an optional boolean flag. If fetch is enabled, the object is fetched
also (with a certain delay). This is useful for clients, that download byte
ranges only from multiple sources. That behavior results in uncachable objects
otherwise. Care is taken for not fetching objects more than once.

Changes to the config files result in an automatic reload by default.


Watch
-----

You might want to increase the log level in /etc/squid/squid_dedup.conf.::

    $ less +F /var/log/squid/dedup.log


Notes
-----

The gen_openSUSE_dedups utility is meant to be executed as a user by
crontab, e.g.::

    $ touch /etc/squid/dedup/opensuse.conf
    $ chown user:group /etc/squid/dedup/opensuse.conf
    $ chmod 644 /etc/squid/dedup/opensuse.conf
    $ su - user
    > crontab -e

Add a line similar to::

    0 6 * * * /usr/bin/gen_openSUSE_dedups -vs


Credits
-------

The basic idea and a reference implementation in PHP was done from Per Jessen.

**Per, thank you for the valuable discussions on this topic.**
