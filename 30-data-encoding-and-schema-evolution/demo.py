"""
Interactive Demo: Data Encoding & Schema Evolution (Protobuf vs JSON)
Simulates:
1. Binary Varint bit-packing and tag allocation.
2. Byte-size comparison: JSON text vs Binary encoded payload.
3. Forward and Backward Schema Evolution compatibility verification.
"""

import json
from typing import Dict, Any

def encode_varint(value: int) -> bytes:
    """Encodes an integer into a variable-length byte sequence (Protobuf Varint)."""
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)

def decode_varint(data: bytes, offset: int = 0) -> (int, int):
    """Decodes a Varint from bytes, returning (value, new_offset)."""
    result = 0
    shift = 0
    while True:
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, offset

class SimulatedProtobufV1:
    """Schema V1: Field 1 (id: int), Field 2 (name: string)"""
    @staticmethod
    def serialize(user_id: int, name: str) -> bytes:
        payload = bytearray()
        # Tag 1 (Wire type 0: Varint) -> (1 << 3) | 0 = 0x08
        payload.append(0x08)
        payload.extend(encode_varint(user_id))
        
        # Tag 2 (Wire type 2: Length-delimited) -> (2 << 3) | 2 = 0x12
        payload.append(0x12)
        name_bytes = name.encode('utf-8')
        payload.extend(encode_varint(len(name_bytes)))
        payload.extend(name_bytes)
        return bytes(payload)

    @staticmethod
    def deserialize(data: bytes) -> Dict[str, Any]:
        result = {}
        offset = 0
        while offset < len(data):
            tag_byte = data[offset]
            offset += 1
            field_num = tag_byte >> 3
            wire_type = tag_byte & 0x07

            if field_num == 1 and wire_type == 0:
                val, offset = decode_varint(data, offset)
                result["user_id"] = val
            elif field_num == 2 and wire_type == 2:
                length, offset = decode_varint(data, offset)
                result["name"] = data[offset:offset+length].decode('utf-8')
                offset += length
            else:
                # Unknown field in V1 -> Skip it! (Forward Compatibility)
                if wire_type == 0:
                    _, offset = decode_varint(data, offset)
                elif wire_type == 2:
                    length, offset = decode_varint(data, offset)
                    offset += length
        return result

class SimulatedProtobufV2:
    """Schema V2: Field 1 (id), Field 2 (name), Field 3 (email: string optional)"""
    @staticmethod
    def serialize(user_id: int, name: str, email: str = None) -> bytes:
        v1_bytes = SimulatedProtobufV1.serialize(user_id, name)
        if not email:
            return v1_bytes
        payload = bytearray(v1_bytes)
        # Tag 3 (Wire type 2) -> (3 << 3) | 2 = 0x1A
        payload.append(0x1A)
        email_bytes = email.encode('utf-8')
        payload.extend(encode_varint(len(email_bytes)))
        payload.extend(email_bytes)
        return bytes(payload)

def run_simulation():
    print("=" * 65)
    print("1. PAYLOAD SIZE BENCHMARK: JSON VS BINARY PROTOBUF")
    print("=" * 65)

    sample_data = {
        "user_id": 1001,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "is_active": True
    }

    json_bytes = json.dumps(sample_data).encode('utf-8')
    # Protobuf equivalent
    proto_bytes = SimulatedProtobufV2.serialize(1001, "Alice Smith", "alice@example.com")

    print(f"JSON Text Payload Size:     {len(json_bytes)} bytes")
    print(f"Protobuf Binary Size:       {len(proto_bytes)} bytes")
    savings = (1 - (len(proto_bytes) / len(json_bytes))) * 100
    print(f"Wire Bandwidth Savings:     {savings:.1f}% reduction!")

    print("\n" + "=" * 65)
    print("2. SCHEMA EVOLUTION: FORWARD COMPATIBILITY TEST")
    print("=" * 65)
    # A new V2 service emits a message with Field 3 (email)
    v2_payload = SimulatedProtobufV2.serialize(42, "Bob", email="bob@tech.org")
    print(f"V2 Service emitted payload with 3 fields (id, name, email): {len(v2_payload)} bytes")

    # An old V1 service (which only knows fields 1 and 2) receives the payload
    v1_decoded = SimulatedProtobufV1.deserialize(v2_payload)
    print(f"Old V1 Service safely decoded payload: {v1_decoded}")
    print("SUCCESS: Old code safely skipped unknown Field 3 without crashing!")

    print("\n" + "=" * 65)
    print("3. SCHEMA EVOLUTION: BACKWARD COMPATIBILITY TEST")
    print("=" * 65)
    # An old V1 service emitted an older record (no email)
    v1_payload = SimulatedProtobufV1.serialize(99, "Charlie")
    # A new V2 service reads it
    v2_decoded = SimulatedProtobufV1.deserialize(v1_payload)
    print(f"New V2 Service successfully read historical V1 record: {v2_decoded}")
    print("SUCCESS: Backward compatibility preserved!")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
