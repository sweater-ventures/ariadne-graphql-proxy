import pytest
from graphql import (
    DirectiveLocation,
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    ScalarTypeDefinitionNode,
    ScalarTypeExtensionNode,
    build_ast_schema,
    parse,
)

from ariadne_graphql_proxy.copy_schema import (
    copy_argument_type,
    copy_arguments,
    copy_directive,
    copy_directives,
    copy_enum_type,
    copy_field,
    copy_field_type,
    copy_input_field_type,
    copy_input_type,
    copy_interface_type,
    copy_object_type,
    copy_scalar_type,
    copy_schema,
    copy_schema_types,
    copy_union_type,
)


def test_copy_schema_returns_new_schema_object_with_copied_query_and_mutation(gql):
    schema_str = gql(
        """
        schema {
            query: Query
            mutation: Mutation
        }

        type Query {
            testQuery: Int!
        }

        type Mutation {
            testMutation: String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert copied_schema.query_type
    assert copied_schema.query_type is not schema.query_type
    assert copied_schema.mutation_type
    assert copied_schema.mutation_type is not schema.mutation_type


def test_copy_schema_returns_new_schema_object_with_copied_types(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery(input: TestInputB!): TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
        }

        input TestInputB {
            fieldb: String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert copied_schema.type_map["TestTypeA"]
    assert copied_schema.type_map["TestTypeA"] is not schema.type_map["TestTypeA"]
    assert copied_schema.type_map["TestInputB"]
    assert copied_schema.type_map["TestInputB"] is not schema.type_map["TestInputB"]


def test_copy_schema_returns_new_schema_object_with_copied_directive(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: Float!
        }

        directive @uppercase on FIELD_DEFINITION
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    org_directive = next(filter(lambda d: d.name == "uppercase", schema.directives))
    copied_directive = next(
        filter(lambda d: d.name == "uppercase", copied_schema.directives)
    )
    assert copied_directive
    assert copied_directive is not org_directive


@pytest.mark.parametrize(
    "graphql_type, expected_method_name",
    [
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL2": GraphQLEnumValue(value="VAL2"),
                },
            ),
            "copy_enum_type",
        ),
        (
            GraphQLObjectType(
                name="TypeA", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            "copy_object_type",
        ),
        (
            GraphQLInputObjectType(
                name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
            ),
            "copy_input_type",
        ),
        (
            GraphQLScalarType(name="ScalarName"),
            "copy_scalar_type",
        ),
        (
            GraphQLInterfaceType(
                name="TypeA", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            "copy_interface_type",
        ),
        (
            GraphQLUnionType(name="UnionType", types=()),
            "copy_union_type",
        ),
    ],
)
def test_copy_schema_types_calls_correct_copy_method_for_type(
    mocker, graphql_type, expected_method_name
):
    mocked_copy_method = mocker.patch(
        f"ariadne_graphql_proxy.copy_schema.{expected_method_name}"
    )

    copy_schema_types(GraphQLSchema(types=[graphql_type]))

    assert mocked_copy_method.called


def test_copy_enum_type_returns_new_enum_with_the_same_values():
    graphql_type = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        description="description",
        extensions={},
    )

    copied_type = copy_enum_type(graphql_type)

    assert isinstance(copied_type, GraphQLEnumType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.values == graphql_type.values
    assert copied_type.description == graphql_type.description
    assert copied_type.extensions == graphql_type.extensions


def test_copy_object_type_returns_new_object_with_fields():
    related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_type = GraphQLObjectType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )

    copied_type = copy_object_type({"TypeB": duplicated_related_type}, graphql_type)

    assert isinstance(copied_type, GraphQLObjectType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.fields["fieldA"] is not graphql_type.fields["fieldA"]
    assert isinstance(copied_type.fields["fieldA"], GraphQLField)
    assert copied_type.fields["fieldA"].type == GraphQLString
    assert copied_type.fields["fieldB"] is not graphql_type.fields["fieldB"]
    assert isinstance(copied_type.fields["fieldB"], GraphQLField)
    assert copied_type.fields["fieldB"].type == duplicated_related_type


def test_copy_field_returns_new_object():
    graphql_field = GraphQLField(
        type_=GraphQLString,
        args={},
        resolve=lambda: None,
        subscribe=lambda: None,
        description="description",
        deprecation_reason="reason",
        extensions={"extension1": None},
    )

    copied_type = copy_field({}, graphql_field)

    assert isinstance(copied_type, GraphQLField)
    assert copied_type is not graphql_field
    assert copied_type.type == GraphQLString
    assert copied_type.args == {}
    assert copied_type.resolve == graphql_field.resolve
    assert copied_type.subscribe == graphql_field.subscribe
    assert copied_type.description == graphql_field.description
    assert copied_type.deprecation_reason == graphql_field.deprecation_reason
    assert copied_type.extensions == graphql_field.extensions


def test_test_copy_field_returns_new_object_with_related_type():
    related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_field = GraphQLField(type_=related_type)

    copied_type = copy_field({"TypeB": duplicated_related_type}, graphql_field)

    assert isinstance(copied_type, GraphQLField)
    assert copied_type is not graphql_field
    assert copied_type.type == duplicated_related_type


def test_copy_arguments_returns_dict_with_copies_of_arguments():
    related_argument_type = GraphQLInputObjectType(
        name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    duplicated_related_argument_type = GraphQLInputObjectType(
        name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    arguments = {
        "arg1": GraphQLArgument(
            type_=GraphQLString,
            default_value="default",
            description="arg1 description",
            deprecation_reason="reason",
            out_name="out name",
        ),
        "arg2": GraphQLArgument(type_=related_argument_type),
    }

    copied_arguments = copy_arguments(
        {"TypeA": duplicated_related_argument_type}, arguments
    )

    assert isinstance(copied_arguments["arg1"], GraphQLArgument)
    assert copied_arguments["arg1"] is not arguments["arg1"]
    assert copied_arguments["arg1"].type == GraphQLString
    assert copied_arguments["arg1"].default_value == arguments["arg1"].default_value
    assert copied_arguments["arg1"].description == arguments["arg1"].description
    assert (
        copied_arguments["arg1"].deprecation_reason
        == arguments["arg1"].deprecation_reason
    )
    assert copied_arguments["arg1"].out_name == arguments["arg1"].out_name
    assert isinstance(copied_arguments["arg2"], GraphQLArgument)
    assert copied_arguments["arg2"] is not arguments["arg2"]
    assert copied_arguments["arg2"].type == duplicated_related_argument_type


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLBoolean, GraphQLBoolean),
        (GraphQLString, GraphQLString),
        (GraphQLFloat, GraphQLFloat),
        (GraphQLID, GraphQLID),
        (GraphQLInt, GraphQLInt),
    ],
)
def test_copy_field_type_returns_correct_scalar_type(field_type, expected):
    assert copy_field_type({}, field_type) == expected


@pytest.mark.parametrize(
    "field_type, duplicated_type",
    [
        (
            GraphQLObjectType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLObjectType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
        ),
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
        ),
        (
            GraphQLInterfaceType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLInterfaceType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
        ),
    ],
)
def test_copy_field_type_returns_correct_related_type(field_type, duplicated_type):
    assert (
        copy_field_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_field_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_field_type({}, field_type), expected)


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLBoolean, GraphQLBoolean),
        (GraphQLString, GraphQLString),
        (GraphQLFloat, GraphQLFloat),
        (GraphQLID, GraphQLID),
        (GraphQLInt, GraphQLInt),
    ],
)
def test_copy_argument_type_returns_correct_scalar_type(field_type, expected):
    assert copy_argument_type({}, field_type) == expected


@pytest.mark.parametrize(
    "field_type, duplicated_type",
    [
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
        ),
        (
            GraphQLInputObjectType(
                name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
            ),
            GraphQLInputObjectType(
                name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
            ),
        ),
    ],
)
def test_copy_argument_type_returns_correct_related_type(field_type, duplicated_type):

    assert (
        copy_argument_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_argument_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_argument_type({}, field_type), expected)


def test_copy_input_type():
    related_field_type = GraphQLInputObjectType(
        "InputRelatedType",
        fields={
            "fieldA": GraphQLInputField(
                type_=GraphQLFloat,
            )
        },
    )
    duplicated_related_field_type = GraphQLInputObjectType(
        "InputRelatedType",
        fields={
            "fieldA": GraphQLInputField(
                type_=GraphQLFloat,
            )
        },
    )
    input_type = GraphQLInputObjectType(
        name="InputType",
        fields={
            "field1": GraphQLInputField(
                type_=GraphQLFloat,
                default_value=2.0,
                description="field1 description",
                deprecation_reason="reason",
                out_name="out name",
            ),
            "field2": GraphQLInputField(type_=related_field_type),
        },
    )

    copied_input_type = copy_input_type(
        {"InputRelatedType": duplicated_related_field_type}, input_type
    )

    assert isinstance(copied_input_type, GraphQLInputObjectType)
    assert copied_input_type is not input_type
    assert copied_input_type.name == input_type.name
    assert isinstance(copied_input_type.fields["field1"], GraphQLInputField)
    assert copied_input_type.fields["field1"] is not input_type.fields["field1"]
    assert copied_input_type.fields["field1"].type == GraphQLFloat
    assert (
        copied_input_type.fields["field1"].default_value
        == input_type.fields["field1"].default_value
    )
    assert (
        copied_input_type.fields["field1"].description
        == input_type.fields["field1"].description
    )
    assert (
        copied_input_type.fields["field1"].deprecation_reason
        == input_type.fields["field1"].deprecation_reason
    )
    assert (
        copied_input_type.fields["field1"].out_name
        == input_type.fields["field1"].out_name
    )
    assert isinstance(copied_input_type.fields["field2"], GraphQLInputField)
    assert copied_input_type.fields["field2"] is not input_type.fields["field2"]
    assert copied_input_type.fields["field2"].type == duplicated_related_field_type


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLBoolean, GraphQLBoolean),
        (GraphQLString, GraphQLString),
        (GraphQLFloat, GraphQLFloat),
        (GraphQLID, GraphQLID),
        (GraphQLInt, GraphQLInt),
    ],
)
def test_copy_input_field_type_returns_correct_scalar_type(field_type, expected):
    assert copy_input_field_type({}, field_type) == expected


def test_copy_input_field_type_returns_correct_named_type():
    field_type = GraphQLNamedType("NamedType")
    duplicated_type = GraphQLNamedType("NamedType")
    assert (
        copy_input_field_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_input_field_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_input_field_type({}, field_type), expected)


def test_copy_scalar_type_returns_new_scalar_object():
    scalar_type = GraphQLScalarType(
        name="ScalarName",
        serialize=lambda: None,
        parse_value=lambda: None,
        parse_literal=lambda: None,
        description="description",
        specified_by_url="randomurl.com",
        extensions={"ext1": None},
        ast_node=ScalarTypeDefinitionNode(),
        extension_ast_nodes=[ScalarTypeExtensionNode()],
    )

    copied_type = copy_scalar_type(scalar_type)

    assert isinstance(copied_type, GraphQLScalarType)
    assert copied_type is not scalar_type
    assert copied_type.name == scalar_type.name
    assert copied_type.serialize == scalar_type.serialize
    assert copied_type.parse_value == scalar_type.parse_value
    assert copied_type.parse_literal == scalar_type.parse_literal
    assert copied_type.description == scalar_type.description
    assert copied_type.specified_by_url == scalar_type.specified_by_url
    assert copied_type.extensions == scalar_type.extensions
    assert copied_type.ast_node == scalar_type.ast_node
    assert copied_type.extension_ast_nodes == scalar_type.extension_ast_nodes


def test_copy_interface_type_returns_new_object_with_fields():
    related_type = GraphQLInterfaceType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLInterfaceType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_type = GraphQLInterfaceType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )

    copied_type = copy_interface_type({"TypeB": duplicated_related_type}, graphql_type)

    assert isinstance(copied_type, GraphQLInterfaceType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.fields["fieldA"] is not graphql_type.fields["fieldA"]
    assert isinstance(copied_type.fields["fieldA"], GraphQLField)
    assert copied_type.fields["fieldA"].type == GraphQLString
    assert copied_type.fields["fieldB"] is not graphql_type.fields["fieldB"]
    assert isinstance(copied_type.fields["fieldB"], GraphQLField)
    assert copied_type.fields["fieldB"].type == duplicated_related_type


def test_copy_union_type_returns_copy_of_union_with_copies_of_subtypes():
    subtype1 = GraphQLObjectType(
        name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
    )
    duplicated_subtype1 = GraphQLObjectType(
        name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
    )
    subtype2 = GraphQLObjectType(
        name="TypeB", fields={"valB": GraphQLField(type_=GraphQLString)}
    )
    duplicated_subtype2 = GraphQLObjectType(
        name="TypeB", fields={"valB": GraphQLField(type_=GraphQLString)}
    )
    union_type = GraphQLUnionType(name="UnionType", types=[subtype1, subtype2])

    copied_union_type = copy_union_type(
        {"TypeA": duplicated_subtype1, "TypeB": duplicated_subtype2}, union_type
    )

    assert isinstance(copied_union_type, GraphQLUnionType)
    assert copied_union_type is not union_type
    assert copied_union_type.types == (duplicated_subtype1, duplicated_subtype2)


def test_copy_directives_calls_copy_directive_for_each_object(mocker):
    directive1 = GraphQLDirective(
        name="testDirective", locations=(DirectiveLocation.FIELD,)
    )
    directive2 = GraphQLDirective(
        name="testDirective", locations=(DirectiveLocation.OBJECT,)
    )
    mocked_copy_directive = mocker.patch(
        "ariadne_graphql_proxy.copy_schema.copy_directive"
    )

    copy_directives({}, (directive1, directive2))

    assert mocked_copy_directive.call_count == 2
    assert mocked_copy_directive.called_with({}, directive1)
    assert mocked_copy_directive.called_with({}, directive2)


def test_copy_directive_returns_new_directive_object():
    related_arg_type = GraphQLInputObjectType(
        name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
    )
    duplicated_related_arg_type = GraphQLInputObjectType(
        name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
    )
    directive = GraphQLDirective(
        name="testDirective",
        locations=(DirectiveLocation.FIELD, DirectiveLocation.OBJECT),
        args={
            "arg1": GraphQLArgument(
                type_=GraphQLString, description="arg1 description"
            ),
            "arg2": GraphQLArgument(type_=related_arg_type),
        },
        is_repeatable=True,
        description="description",
        extensions={"ext": None},
    )

    copied_directive = copy_directive(
        {"InputType": duplicated_related_arg_type}, directive
    )

    assert isinstance(copied_directive, GraphQLDirective)
    assert copied_directive is not directive
    assert copied_directive.name == directive.name
    assert copied_directive.locations == directive.locations
    assert isinstance(copied_directive.args["arg1"], GraphQLArgument)
    assert copied_directive.args["arg1"].type == GraphQLString
    assert copied_directive.args["arg1"].description == "arg1 description"
    assert isinstance(copied_directive.args["arg2"], GraphQLArgument)
    assert copied_directive.args["arg2"].type == duplicated_related_arg_type
    assert copied_directive.is_repeatable == directive.is_repeatable
    assert copied_directive.description == directive.description
    assert copied_directive.extensions == directive.extensions
