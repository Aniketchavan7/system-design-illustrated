"""One-shot producer, outbox relay, consumer, and crash recovery exercise."""

import argparse
import os
import subprocess
import sys
from contextlib import contextmanager
from uuid import UUID, uuid4

import pika
import psycopg


def database():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5)


@contextmanager
def broker(queue):
    parameters = pika.URLParameters(os.environ["AMQP_URL"])
    parameters.socket_timeout = 5
    parameters.blocked_connection_timeout = 10
    with pika.BlockingConnection(parameters) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        yield channel


def create(order_id):
    with database() as conn:
        conn.execute(
            "INSERT INTO orders VALUES (%s) ON CONFLICT DO NOTHING", (order_id,)
        )
        conn.execute(
            "INSERT INTO order_outbox (event_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (order_id,),
        )
    print(f"Order and outbox recorded: {order_id}")


def relay(queue, order_id, crash_after_publish):
    with database() as conn:
        row = conn.execute(
            """
            SELECT event_id FROM order_outbox
            WHERE event_id = %s AND published_at IS NULL
            FOR UPDATE SKIP LOCKED
            """,
            (order_id,),
        ).fetchone()
        if row is None:
            print("No available unpublished event for this order.")
            return

        with broker(queue) as channel:
            channel.confirm_delivery()
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=str(order_id).encode("ascii"),
                mandatory=True,
                properties=pika.BasicProperties(
                    message_id=str(order_id), delivery_mode=2
                ),
            )
            print(f"Broker confirmed: {order_id}", flush=True)
            if crash_after_publish:
                os._exit(41)

        conn.execute(
            "UPDATE order_outbox SET published_at = now() WHERE event_id = %s",
            (order_id,),
        )


def worker(queue, crash_after_commit):
    with broker(queue) as channel:
        delivery, _, body = channel.basic_get(queue, auto_ack=False)
        if delivery is None:
            print("Queue is empty.")
            return

        order_id = UUID(body.decode("ascii"))
        with database() as conn:
            applied = conn.execute(
                "INSERT INTO fulfillments (order_id) VALUES (%s) "
                "ON CONFLICT DO NOTHING RETURNING order_id",
                (order_id,),
            ).fetchone()

        action = "Fulfilled" if applied else "Skipped duplicate"
        print(f"{action}: {order_id} (redelivered={delivery.redelivered})", flush=True)
        if crash_after_commit:
            os._exit(42)
        channel.basic_ack(delivery.delivery_tag)


def order_status(order_id):
    with database() as conn:
        return conn.execute(
            """
            SELECT box.published_at IS NOT NULL,
                   (SELECT count(*) FROM fulfillments WHERE order_id = box.event_id)
            FROM order_outbox AS box WHERE box.event_id = %s
            """,
            (order_id,),
        ).fetchone()


def verify():
    order_id = uuid4()
    queue = f"verify-{order_id}"

    def run(*args, expected=0):
        result = subprocess.run(
            [sys.executable, "-u", __file__, "--queue", queue, *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout, end="")
        if result.returncode != expected:
            raise RuntimeError(
                f"{args} exited {result.returncode}, expected {expected}: {result.stderr}"
            )
        return result.stdout

    try:
        run("create", str(order_id))
        run("create", str(order_id))
        run("relay", str(order_id), "--crash-after-publish", expected=41)
        if order_status(order_id) != (False, 0):
            raise RuntimeError("The interrupted relay should leave a pending outbox event.")

        run("relay", str(order_id))
        first_attempt = run("worker", "--crash-after-commit", expected=42)
        if "Fulfilled:" not in first_attempt or order_status(order_id) != (True, 1):
            raise RuntimeError("The first worker should commit a single fulfillment.")

        retries = run("worker") + run("worker")
        if retries.count("Skipped duplicate:") != 2 or "redelivered=True" not in retries:
            raise RuntimeError("Expected a republished event and a broker redelivery.")
        if "Queue is empty." not in run("worker") or order_status(order_id) != (True, 1):
            raise RuntimeError("Expected an empty queue and exactly one fulfillment.")
        print("Verified both crash windows, two skipped duplicates, and one fulfillment.")
    finally:
        with broker(queue) as channel:
            channel.queue_delete(queue=queue)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", default="orders")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("create").add_argument("order_id", type=UUID)
    relay_parser = commands.add_parser("relay")
    relay_parser.add_argument("order_id", type=UUID)
    relay_parser.add_argument("--crash-after-publish", action="store_true")
    commands.add_parser("worker").add_argument("--crash-after-commit", action="store_true")
    commands.add_parser("status").add_argument("order_id", type=UUID)
    commands.add_parser("verify")
    args = parser.parse_args()

    if args.command == "create":
        create(args.order_id)
    elif args.command == "relay":
        relay(args.queue, args.order_id, args.crash_after_publish)
    elif args.command == "worker":
        worker(args.queue, args.crash_after_commit)
    elif args.command == "status":
        status = order_status(args.order_id)
        if status is None:
            parser.error("Unknown order ID")
        published, count = status
        print(f"Published: {published}, fulfillment rows: {count}")
    else:
        verify()


if __name__ == "__main__":
    main()
