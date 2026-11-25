# Real-World Case Studies: Data Encoding and Schema Evolution

> ✅ **Source-checked.** Each deep dive names its source, and we kept only what that source says. Found an error, or something the source doesn't support? [Report it on the tracking issue](https://github.com/Aniketchavan7/system-design-illustrated/issues/9).

> Two ways to keep old and new code talking: Protocol Buffers tag every field with a permanent number, while Avro sends no field identifiers at all and relies on the reader knowing the writer's schema, which is what a schema registry is for.

---

## 🏢 Deep Dive 1: Protocol Buffers at Google

> **Sources:** protobuf.dev: [Overview](https://protobuf.dev/overview/), [History](https://protobuf.dev/history/), [Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/). Everything in this section comes from those pages.

- **Background.** "The initial version of Protobuf ('Proto1') was developed starting in early 2001." It was open-sourced in 2008, and "Protobuf is the most commonly-used data format at Google."
- **Field numbers are forever.** A field's number "cannot be changed once your message type is in use because it identifies the field in the message wire format", and "field numbers should never be reused".
- **Reserve what you delete.** When you remove a field, "you must reserve the deleted field number". Reserving the name too keeps JSON and text-format encodings parsing.
- **Compatibility both ways.** "Old code will read new messages without issues, ignoring any newly added fields", and "new code will also transparently read old messages." Proto3 also keeps unknown fields when it re-serializes a message, though some operations, such as converting to JSON, drop them.

---

## 🪶 Deep Dive 2: Apache Avro, No Tags on the Wire

> **Source:** the [Apache Avro 1.11.1 specification](https://avro.apache.org/docs/1.11.1/specification/). Everything in this section comes from it.

- **Compact encoding.** "Binary encoding does not include field names", and a record is "just the concatenation of the encodings of its fields". Without the schema, the bytes are meaningless.
- **Reading needs the writer's schema.** The reader resolves "the writer's schema" against its own, and "fields are matched by name".
- **Evolving safely.** If the reader expects a field the writer didn't send, "the reader should use the default value from its field", and with no default "an error is signalled". If the writer sent a field the reader doesn't know, "the writer's value for that field is ignored."

---

## 🗃️ Deep Dive 3: Confluent Schema Registry, Finding the Writer's Schema

> **Sources:** Confluent docs, [Schema evolution and compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) and [Formats, serializers and deserializers](https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html). Everything in this section comes from those pages.

- **Wire format.** Each message starts with a version byte (`0`), then a "4-byte schema ID as returned by Schema Registry" in big-endian order, then the data. (Protobuf messages also carry message indexes before the data.) The consumer uses the ID to fetch the writer's schema.
- **Compatibility checks.** The registry can enforce `BACKWARD`, `FORWARD`, `FULL`, their `_TRANSITIVE` variants, or `NONE`. "The default compatibility mode is BACKWARD", which checks only against the previous version, not all versions.

> ℹ️ An earlier version of this page said "100%" of Google's internal traffic uses Protocol Buffers at "billions of RPCs per second", and that LinkedIn and Netflix move "1.5 trillion events per day" through Avro. The sources above don't support those figures, so we removed them.

---

## ⚖️ Side by Side

| | Protocol Buffers | Avro + Schema Registry |
| :--- | :--- | :--- |
| **How a field is identified** | A permanent field number on the wire | Its name, matched between writer and reader schemas |
| **What travels with each message** | Field numbers with the values | A 4-byte schema ID, then bare values |
| **Main evolution rule** | Never change or reuse a field number | Give new fields defaults, and let the registry check compatibility |

---

## 🎯 System Design Interview Takeaways
1. **Rolling deploys need both directions.** New code must read old data (backward compatibility), and old code must read new data (forward compatibility).
2. **With Protobuf, the number is the contract.** Names are for humans. Never change or reuse a field number, and reserve deleted ones.
3. **With Avro, defaults are the contract.** Add fields with defaults, and use a registry so consumers can always find the writer's schema.
