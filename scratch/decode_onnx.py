import struct

def parse_proto_fields(data):
    pos = 0
    fields = []
    while pos < len(data):
        # read varint key
        key = 0
        shift = 0
        while True:
            if pos >= len(data): break
            b = data[pos]
            pos += 1
            key |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
        field_num = key >> 3
        wire_type = key & 0x07
        if wire_type == 0: # Varint
            val = 0
            shift = 0
            while True:
                b = data[pos]
                pos += 1
                val |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            fields.append((field_num, wire_type, val))
        elif wire_type == 1: # 64-bit
            val = data[pos:pos+8]
            pos += 8
            fields.append((field_num, wire_type, val))
        elif wire_type == 2: # Length-delimited
            length = 0
            shift = 0
            while True:
                b = data[pos]
                pos += 1
                length |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            val = data[pos:pos+length]
            pos += length
            fields.append((field_num, wire_type, val))
        elif wire_type == 5: # 32-bit
            val = data[pos:pos+4]
            pos += 4
            fields.append((field_num, wire_type, val))
        else:
            break
    return fields

# Let's inspect student.onnx
with open("web/model/student.onnx", "rb") as f:
    raw = f.read()

model_fields = parse_proto_fields(raw)
graph_data = None
for fnum, wtype, val in model_fields:
    if fnum == 1:
        print("IR Version:", val)
    elif fnum == 2:
        print("Producer Name:", val.decode('utf-8', errors='ignore'))
    elif fnum == 7:
        graph_data = val

if graph_data:
    graph_fields = parse_proto_fields(graph_data)
    # in GraphProto:
    # 2: name (string)
    # 5: initializer (repeated TensorProto)
    # 11: input (repeated ValueInfoProto)
    # 12: output (repeated ValueInfoProto)
    # 1: node (repeated NodeProto)
    nodes = []
    inputs = []
    outputs = []
    initializers = []
    for fnum, wtype, val in graph_fields:
        if fnum == 2:
            print("Graph Name:", val.decode('utf-8', errors='ignore'))
        elif fnum == 11:
            inputs.append(val)
        elif fnum == 12:
            outputs.append(val)
        elif fnum == 1:
            nodes.append(val)
        elif fnum == 5:
            initializers.append(val)
    print(f"Graph has {len(nodes)} nodes, {len(inputs)} inputs, {len(outputs)} outputs, {len(initializers)} initializers.")

    # Inspect input names
    for i, inp in enumerate(inputs):
        inp_fields = parse_proto_fields(inp)
        name = [v.decode('utf-8', errors='ignore') for fn, wt, v in inp_fields if fn == 1]
        print(f"Input {i}: Name = {name}")

    # Inspect output names
    for i, out in enumerate(outputs):
        out_fields = parse_proto_fields(out)
        name = [v.decode('utf-8', errors='ignore') for fn, wt, v in out_fields if fn == 1]
        print(f"Output {i}: Name = {name}")

    # Inspect initializers data types (in TensorProto, field 2 is data_type: 1=FLOAT, 2=UINT8, 3=INT8, 7=INT64)
    data_types = {}
    for init in initializers:
        init_fields = parse_proto_fields(init)
        for fn, wt, v in init_fields:
            if fn == 2: # data_type
                data_types[v] = data_types.get(v, 0) + 1
    type_map = {1: "FLOAT", 2: "UINT8", 3: "INT8", 4: "UINT16", 5: "INT16", 6: "INT32", 7: "INT64", 9: "BOOL", 10: "FLOAT16"}
    print("Initializer data types:", {type_map.get(k, k): v for k, v in data_types.items()})

    # Check node op_types (in NodeProto, field 4 is op_type string)
    op_types = {}
    for node in nodes:
        node_fields = parse_proto_fields(node)
        for fn, wt, v in node_fields:
            if fn == 4:
                op = v.decode('utf-8', errors='ignore')
                op_types[op] = op_types.get(op, 0) + 1
    print("Node op types top 15:", sorted(op_types.items(), key=lambda x: -x[1])[:15])

