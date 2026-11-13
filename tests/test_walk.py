from schemacheck.walk import walk


def test_walk_yields_all_subschemas_with_pointers_and_depth():
    schema = {
        "properties": {"a/b": {"items": {"type": "string"}}, "m~n": {"anyOf": [{}, {"not": {}}]}},
        "additionalProperties": {"type": "integer"},
        "$defs": {"D": {"prefixItems": [{}]}},
        "definitions": {"E": {}},
        "if": {},
        "then": {},
        "else": {},
        "allOf": [{}],
        "oneOf": [{}],
    }
    got = {p: d for _, p, d in walk(schema)}
    assert got[""] == 0
    assert got["/properties/a~1b"] == 1
    assert got["/properties/a~1b/items"] == 2
    assert got["/properties/m~0n/anyOf/1/not"] == 3
    for p in ["/additionalProperties", "/$defs/D/prefixItems/0", "/definitions/E", "/if",
              "/then", "/else", "/allOf/0", "/oneOf/0"]:
        assert p in got


def test_walk_prefix_and_non_dict():
    assert [p for _, p, _ in walk({"items": {}}, "/x")] == ["/x", "/x/items"]
    assert list(walk(True)) == []


def test_recursive_ref_does_not_hang():
    schema = {
        "$ref": "#/$defs/N",
        "$defs": {"N": {"properties": {"next": {"$ref": "#/$defs/N"}, "self": {"$ref": "#"}}}},
    }
    pointers = [p for _, p, _ in walk(schema)]
    assert pointers == ["", "/$defs/N", "/$defs/N/properties/next", "/$defs/N/properties/self"]
