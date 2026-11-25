# Real-World Case Studies: Time, Clocks and Ordering

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Three answers to "what happened first?": Lamport's logical clocks, Google's TrueTime with bounded uncertainty, and Amazon Dynamo's vector clocks.

---

## 🕰️ Deep Dive 1: Lamport Clocks, Ordering Without Real Time

> **Source:** Leslie Lamport, ["Time, Clocks, and the Ordering of Events in a Distributed System"](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) (Communications of the ACM, 1978). Everything in this section comes from the paper.

- **Partial order.** "The relation 'happened before' is therefore only a partial ordering of the events in the system." Two events on different machines with no message between them are concurrent: neither happened first.
- **Logical clocks.** Lamport's clocks satisfy the **Clock Condition**: "For any events a, b: if a ---> b then C(a) < C(b)." The converse doesn't hold, so a smaller timestamp doesn't prove one event caused another.

---

## 🏢 Deep Dive 2: Google TrueTime, Real Time with Known Error

> **Source:** [Spanner: Google's Globally-Distributed Database](https://www.usenix.org/conference/osdi12/technical-sessions/presentation/corbett) (Corbett et al., OSDI 2012). Everything in this section comes from the paper.

- **An interval, not a number.** `TT.now()` returns an interval `[earliest, latest]` "guaranteed to contain the absolute time during which TT.now() was invoked".
- **Two kinds of reference.** "The underlying time references used by TrueTime are GPS and atomic clocks", used together "because they have different failure modes".
- **Small uncertainty.** The uncertainty ε is "typically a sawtooth function of time, varying from about 1 to 7 ms over each poll interval", so "4 ms most of the time". Servers poll time masters every 30 seconds.
- **Commit wait.** Spanner doesn't make a commit visible until its timestamp is definitely in the past. That turns bounded clock error into a guarantee about ordering (see module 14).

---

## 🛒 Deep Dive 3: Amazon Dynamo, Vector Clocks and the Shopping Cart

> **Source:** [Dynamo: Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/2007/10/amazons_dynamo.html) (DeCandia et al., SOSP 2007). Everything in this section comes from the paper.

- **Capturing causality.** "Dynamo uses vector clocks in order to capture causality between different versions of the same object." If neither version descends from the other, they're concurrent, and both are kept.
- **Reconciling in the application.** For the shopping cart, "an 'Add to Cart' operation can never be forgotten or rejected", so the cart's business logic "reconciles objects by merging different versions of a customer's shopping cart."
- **The honest trade-off.** With that merge, "an 'add to cart' operation is never lost. However, deleted items can resurface."
- **The simpler alternative.** Other applications use timestamp-based reconciliation, where the latest timestamp simply wins.

---

> ℹ️ An earlier version of this page claimed NTP drifts "100ms to 250ms" across continents and that before TrueTime "no distributed database" could offer global serializable transactions. We couldn't source either claim, so we removed them.

## 🎯 System Design Interview Takeaways
1. **Physical clocks can't order events reliably.** Use logical clocks for causality, or bound the error explicitly as TrueTime does.
2. **Last-write-wins silently drops writes.** If two concurrent updates both matter, keep both (vector clocks) and merge them.
3. **Merging has costs too.** Dynamo's cart never loses an add, but a deleted item can come back. Say which failure your design accepts.
