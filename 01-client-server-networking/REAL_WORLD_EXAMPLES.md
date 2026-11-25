# Client–server networking in production

> ✅ **Source-checked.** Every claim links to its source, and we checked each one against it. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

## Google · QUIC deployment

At SIGCOMM in 2017, Google researchers described an early deployment of QUIC on thousands of Google servers, including traffic from Chrome and YouTube. The design used an encrypted, multiplexed transport and allowed Google to iterate on transport behavior. The deployment figures describe the system studied in that paper. [Google's 2017 QUIC deployment paper](https://research.google/pubs/the-quic-transport-protocol-design-and-internet-scale-deployment/)

The later IETF standards specify QUIC version 1 and HTTP/3 over QUIC. QUIC delivers bytes in order within a stream. When one stream is missing data, an unrelated stream can continue delivering its own available data. Connection-wide limits, including congestion control, can still affect more than one stream. [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html) · [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)

**Apply it to Trail Notes.** If the browser downloads the guide and a photo on separate streams, losing part of the photo should not force the transport to wait for the missing photo bytes before delivering available guide bytes.

## Netflix · A gateway proxies the request

Netflix's engineering documentation describes Zuul 2 as a Netty server that runs inbound filters, proxies the request through a Netty client, and runs outbound filters before sending the response. The inbound and upstream connections are distinct. [Netflix's Zuul 2 architecture](https://github.com/Netflix/zuul/wiki/How-It-Works-2.0)

**Apply it to Trail Notes.** When an edge gateway sits in front of the site, trace the browser-to-gateway hop and the gateway-to-backend hop separately. Each hop can have its own latency, connection setup, and timeout. This is an illustrative design exercise.

[Return to the networking lesson](./README.md#first-pass)
