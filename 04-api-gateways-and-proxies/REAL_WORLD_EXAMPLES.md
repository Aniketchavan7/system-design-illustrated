# Real-World Case Studies: API Gateways and Proxies

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> How **Netflix** structures its Zuul gateway as a chain of filters, and how the **Envoy** proxy (built at Lyft, now used in Google Cloud's service mesh) gets its configuration from a control plane.

---

## 🎬 Deep Dive 1: Netflix Zuul, a Gateway Built from Filters

> **Sources:** the Zuul project wiki on GitHub: [How it Works](https://github.com/Netflix/zuul/wiki/How-it-Works) (Zuul 1), [How It Works 2.0](https://github.com/Netflix/zuul/wiki/How-It-Works-2.0), [How It Works 3.0](https://github.com/Netflix/zuul/wiki/How-It-Works-3.0), [Filters](https://github.com/Netflix/zuul/wiki/Filters) and [Filters (legacy)](https://github.com/Netflix/zuul/wiki/Filters-legacy). Everything in this section comes from those pages.

### 1. The original design: a chain of filters
In the first version of Zuul, "at the center of Zuul is a series of Filters". Each request passes through filter stages, and filters "share state through a RequestContext which is unique to each request":

| Stage | What it does (wiki wording) |
| :--- | :--- |
| **PRE** | runs "before routing to the origin" |
| **ROUTING** | builds the origin request and sends it "using Apache HttpClient or Netflix Ribbon" |
| **POST** | runs "after the request has been routed to the origin" |
| **ERROR** | runs "when an error occurs during one of the other phases" |

Filters were written in Groovy and could be changed without a restart: the source files were "periodically polled for changes" and "dynamically compiled into the running server". The wiki gives no polling interval. Zuul 3 removed this dynamic loading; filters are now compiled into the application.

### 2. The Netty design
The 2.0 and 3.0 pages describe Zuul as "a Netty server that runs pre-filters (inbound filters)", then "proxies the request using a Netty client", then "returns the response after running post-filters (outbound filters)".

```
[ Client ] ──► [ Inbound filters ] ──► [ Endpoint: proxy via Netty client ] ──► [ Origin service ]
                                                                                      │
[ Client ] ◄── [ Outbound filters ] ◄──────────────────────────────────────────────────┘
```

- **Inbound** filters "execute before routing to the origin". **Endpoint** filters proxy the request, or can "return static responses". **Outbound** filters "execute after getting the response from the origin".
- Because the server runs on an event loop, "it's CRITICAL to never block in a filter". Work that must block belongs in an **async** filter on a separate thread pool. Everything else can be a plain **sync** filter.

### 3. What this teaches
One slow call inside an event-loop gateway stalls every other connection on that loop. That's why Zuul splits filters into sync ones, which must be fast, and async ones for anything that waits.

> ℹ️ An earlier version of this page quoted traffic figures (100+ billion requests a day, 2+ million connections, 50,000 idle connections per instance), said rules propagate "within 5 seconds", and described an internal "Passport" token. None of that appears in the sources above, so we removed it. Netflix's tech blog covers the Zuul 1 to Zuul 2 move in more depth. A sourced summary would be a welcome contribution.

---

## 🛰️ Deep Dive 2: Envoy and xDS, a Proxy Programmed by a Control Plane

> **Sources:** CNCF, ["CNCF hosts Envoy"](https://www.cncf.io/blog/2017/09/13/cncf-hosts-envoy/) (13 September 2017); Envoy docs: [What is Envoy](https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy), [Threading model](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/threading_model), [xDS protocol](https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol); Google Cloud: [Cloud Service Mesh overview](https://docs.cloud.google.com/service-mesh/docs/overview).

### 1. Where Envoy comes from
Envoy was "originally built at Lyft to move their architecture away from a monolith" and was "written in C++ for performance reasons" (CNCF). Lyft open-sourced it in September 2016. By the time it joined the CNCF in 2017, other companies contributed too: "there are now more people working on Envoy at Google than there are at Lyft."

The docs describe it as "an L7 proxy and communication bus designed for large modern service oriented architectures" and "a self contained process that is designed to run alongside every application server". Because it runs as a separate process, one deployment can "form a mesh between Java, C++, Go, PHP, Python, etc."

### 2. Threading
Envoy uses "a 'single process, multiple threads' architecture": one main thread for coordination and a configurable number of worker threads that do the actual listening and forwarding. "When a connection is accepted by a listener, it is bound to a single worker thread for its entire lifetime." The docs recommend one worker per hardware thread.

### 3. Configuration from a control plane: xDS
Instead of a static config file, Envoy "discovers its various dynamic resources via the filesystem or by querying one or more management servers". These discovery APIs are collectively called **xDS**:

| API | Resource it delivers |
| :--- | :--- |
| **LDS**: Listener Discovery Service | `Listener`: the ports and sockets Envoy listens on |
| **RDS**: Route Discovery Service | `RouteConfiguration`: HTTP routing rules |
| **CDS**: Cluster Discovery Service | `Cluster`: the upstream services |
| **EDS**: Endpoint Discovery Service | `ClusterLoadAssignment`: the hosts in each cluster |
| **SDS**: Secret Discovery Service | `Secret`: certificates and keys |

The resources chain together: a listener points to a route configuration, which points to clusters, and each cluster points to its endpoints. Updates arrive by watching a file, over gRPC streams, or by polling a REST-JSON endpoint. With **ADS**, "a single management server, via a single gRPC stream" delivers every type.

### 4. Google Cloud's service mesh uses it
In Google Cloud Service Mesh, "Envoy proxies and proxyless gRPC both use the xDS API to connect to the control plane" (when the mesh is configured with Google Cloud APIs). The docs say Anthos Service Mesh and Traffic Director "converged into Cloud Service Mesh" in May 2024.

> ℹ️ An earlier version of this page called Envoy a Google proxy and claimed Google's internal infrastructure runs "trillions of RPCs daily" through it, with SPIFFE certificates rotated "every few hours". The sources show Envoy was built at Lyft, and none of them support the other claims, so we removed them.

---

## ⚖️ Side by Side

| | Netflix Zuul | Envoy |
| :--- | :--- | :--- |
| **Built with** | Java, Netty (2.0/3.0 design) | C++ |
| **Where it runs** | As a gateway in front of origin services | As a separate process next to each application, or at the edge |
| **How behaviour is extended** | Filters in any JVM language; Groovy filters were hot-loaded until Zuul 3 | Configuration streamed from a management server over xDS |
| **Language of the services behind it** | Any (it proxies HTTP) | Any: it runs out of process |

---

## 🎯 System Design Interview Takeaways
1. **Never block the event loop.** In a non-blocking gateway, a slow call in the request path stalls every connection sharing that thread. Push blocking work to a separate pool, as Zuul's async filters do.
2. **Authenticate once at the edge.** A common pattern is for the gateway to validate the client's token and pass a signed internal identity downstream, so internal services don't each re-check the original credential. This is general practice, not a claim about any one company.
3. **Keep cross-cutting concerns in the gateway.** Routing, TLS termination, rate limiting and request IDs belong there. Business logic does not.
4. **Separate the data plane from the control plane.** Proxies handle traffic. A control plane tells them what to do, via an API such as xDS, so routing changes don't need a redeploy.
