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
