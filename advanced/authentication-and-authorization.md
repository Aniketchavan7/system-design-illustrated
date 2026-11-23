# Authentication and authorization

Authentication establishes who is asking. Authorization checks whether that identity may perform a given action on a resource. A library card identifies a reader. A separate staff permission controls who can edit the catalog.

## Follow a browser sign-in

In OpenID Connect, the ID token conveys identity information to the client. The access token is for the intended API. A server-rendered app can keep provider tokens on the server and give the browser an opaque session cookie.

~~~mermaid
sequenceDiagram
    participant B as Browser
    participant A as Application
    participant I as Identity provider
    participant D as Data store
    B->>A: Start sign-in
    A-->>B: Redirect with state and PKCE challenge
    B->>I: Authenticate
    I-->>B: Redirect with authorization code
    B->>A: Return code and state
    A->>I: Exchange code with PKCE verifier
    I-->>A: Return tokens
    A->>A: Validate ID token and create session
    A-->>B: Set session cookie
    B->>A: Request invoice with session cookie
    A->>D: Load invoice within authorized tenant
    A-->>B: Return permitted data
~~~

Use an established identity provider and protocol library. Validate the sign-in response and the token claims appropriate to the protocol, including issuer, audience, expiry, and nonce when used. Set browser cookies with `Secure` and `HttpOnly`, choose a suitable `SameSite` setting, and protect state-changing requests against CSRF. [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html) · [OAuth security best current practice](https://www.rfc-editor.org/rfc/rfc9700.html)

| Model | How a request is checked | What changes on logout or revocation? |
| --- | --- | --- |
| Opaque session | Look up the session in a shared store | Invalidate the session record. |
| Self-contained API token | Check the signature and required claims using trusted verification keys | Short expiry limits the remaining window. Immediate revocation requires an online check or equivalent enforcement. |

Refresh token rotation invalidates the previous refresh token. A previously issued access token can still be usable until expiry unless the receiving service checks its revocation state. Scope access tokens to their intended audience.

## Enforce authorization at the resource

Suppose Maya can read invoices for tenant A. A request must establish that the invoice belongs to tenant A, that Maya still belongs to tenant A, and that her role permits invoice reads. Apply all of those checks when loading the resource. Consider the same rules for exports, background jobs, and cache keys.

- **Role-based access** grants permissions through roles such as billing reader.
- **Attribute-based access** evaluates facts such as resource sensitivity and the actor's classification.
- **Relationship-based access** follows a relationship such as a user belonging to a team that can read a document. [Google Zanzibar paper](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)

For service-to-service calls, give workloads separate identities and short-lived credentials intended for the receiving service. Mutual TLS can authenticate both ends. The receiving service still needs an authorization rule. When a service acts for a user, check both the service's privileges and the user's delegated authority. [SPIFFE workload identity](https://spiffe.io/docs/latest/spiffe-about/overview/)

## Try it yourself

From the repository root run `python advanced/auth_demo.py`. The standard-library example models policy after sign-in. It checks an opaque session, looks up the invoice's tenant, and checks the user's current role. It exercises tenant isolation, membership removal, session expiry, and logout.

**Check yourself.** When a billing role is removed, should a live session still grant access? The example checks current membership on every request, so that session can no longer read the invoice.

[Runnable policy example](./auth_demo.py) · [API gateways](../04-api-gateways-and-proxies/) · [Service mesh](../33-microservices-and-service-mesh/)
