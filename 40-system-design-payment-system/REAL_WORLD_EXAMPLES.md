# Payment systems in production

> ⚠️ **Not yet source-checked.** These case studies summarize public engineering posts and talks, and some details may be simplified or wrong. Before you repeat a specific number or design in an interview, check it against the company's own write-up. Found an error, or a source that confirms a section? [Add it to the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9). Sourced fixes are the most welcome contribution here.

## Stripe · Idempotency and ledger reconciliation

Stripe reported **$1.9 trillion in total volume for 2025**. Its February 2024 engineering article reports **greater than 99.999% Stripe API availability** over the preceding Black Friday through Cyber Monday period. The availability figure describes that event window. [2025 annual letter](https://stripe.com/annual-updates/2025) · [Stripe Ledger engineering write-up](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement)

In API v1, once endpoint execution begins, Stripe can save the response status and body under an idempotency key. While the key is retained, a compatible retry can return that saved result. A validation error before endpoint execution is an example of a result Stripe does not save. [Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests)

Stripe describes Ledger as an immutable event log that represents money movement across its systems and financial partners. Its data quality platform checks flows for clearing, timeliness, and completeness. These checks address what happens after calls to payments APIs. [Stripe Ledger engineering write-up](https://stripe.dev/blog/ledger-stripe-system-for-tracking-and-validating-money-movement)

## PayPal · Retrying a capture

PayPal documents the `PayPal-Request-Id` header for supported REST API operations. It gives payment capture as an example of an operation that can time out after being processed. Retrying with the same ID can return the status of the previous operation. Check the endpoint for support and retention. [PayPal idempotency guide](https://developer.paypal.com/api/rest/reference/idempotency/)

## Worked example · A response is lost

~~~mermaid
sequenceDiagram
    participant C as Checkout service
    participant O as Order store
    participant P as Payment provider
    C->>O: Persist operation ID and pending state
    C->>P: Capture with operation ID
    P->>P: Record capture
    P--xC: Response lost
    C->>P: Retry with the same operation ID
    P-->>C: Return recorded outcome
    C->>O: Record outcome and provider reference
~~~

This is an illustrative merchant design. Write the operation ID before the first request. Reuse it when the outcome is unknown, follow the provider's recovery guidance, and reconcile unresolved attempts against provider status and settlement records. A retry after the provider's retention window needs another way to establish the original outcome before issuing a new charge.
