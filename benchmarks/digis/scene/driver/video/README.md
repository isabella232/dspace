A simple, out-of-the-box LAN RTMP server can be set up using snginx + nginx-rtmp-module.

E.g., https://obsproject.com/forum/resources/how-to-set-up-your-own-private-rtmp-server-using-nginx.50/

The basic steps are:

1. Build and install nginx with the rtmp extension.
2. Start nginx with rtmp module configured, e.g.,

```nginx
rtmp {
        server {
                listen 1935;
                chunk_size 4096;

                application live {
                        live on;
                        record off;
                }
        }
}
```

3. Set a key for the rtmp stream and stream from your cam or any rtmp source to the server.
4. Capture the stream from the local rtmp server.