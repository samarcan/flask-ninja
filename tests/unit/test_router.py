import pytest

from flask_ninja import Query
from flask_ninja.operation import Callback, Operation
from flask_ninja.router import Router
from flask_ninja.utils import create_model_field
from tests.conftest import BearerAuth


def test_add_route_all_params():
    router = Router()
    callback = Callback(
        name="some_name",
        url="some_url",
        method="some_callback_method",
        response_codes={},
    )

    param = create_model_field(name="some_param", type_=int, field_info=Query())

    @router.add_route(
        "GET",
        "/foo",
        responses={200: str},
        auth="some_auth",
        summary="some_summary",
        description="some_description",
        params=[param],
        callbacks=[callback],
    )
    def sample_method():
        return "foo"

    assert len(router.operations) == 1
    assert router.operations[0].path == "/foo"
    assert router.operations[0].method == "GET"
    assert str(router.operations[0].responses) == str(
        {200: create_model_field(name="Response 200", type_=str, required=True)}
    )
    assert router.operations[0].callbacks == [callback]
    assert router.operations[0].summary == "some_summary"
    assert router.operations[0].description == "some_description"
    assert router.operations[0].params == [param]


def test_add_route_no_params():
    router = Router()

    @router.add_route(
        "GET",
        "/foo",
    )
    def sample_method() -> str:
        return "foo"

    assert len(router.operations) == 1
    assert router.operations[0].path == "/foo"
    assert router.operations[0].method == "GET"
    assert str(router.operations[0].responses) == str(
        {200: create_model_field(name="Response 200", type_=str, required=True)}
    )
    assert router.operations[0].callbacks is None
    assert router.operations[0].summary == ""
    assert router.operations[0].description == ""
    assert router.operations[0].params == []


def some_view(foo_param: int) -> str:
    return str(foo_param)


@pytest.mark.parametrize(
    ("router", "another_router", "prefix", "result_operations"),
    [
        pytest.param(Router(), Router(), "/some_prefix", [], id="empty routers"),
        pytest.param(
            Router(),
            Router(operations=[Operation("/ping", "GET", some_view)]),
            "/some_prefix",
            [Operation("/some_prefix/ping", "GET", some_view)],
            id="empty_root_nonempty_add",
        ),
        pytest.param(
            Router(operations=[Operation("/ping", "GET", some_view)]),
            Router(),
            "/some_prefix",
            [Operation("/ping", "GET", some_view)],
            id="nonempty_root_empty_add",
        ),
        pytest.param(
            Router(operations=[Operation("/ping", "GET", some_view)]),
            Router(operations=[Operation("/ping", "GET", some_view)]),
            "/some_prefix",
            [
                Operation("/ping", "GET", some_view),
                Operation("/some_prefix/ping", "GET", some_view),
            ],
            id="not_set_auth_root_not_set_auth_add",
        ),
        pytest.param(
            Router(
                operations=[Operation("/ping", "GET", some_view, auth=None)], auth=None
            ),
            Router(operations=[Operation("/ping", "GET", some_view)]),
            "/some_prefix",
            [
                Operation("/ping", "GET", some_view, auth=None),
                Operation("/some_prefix/ping", "GET", some_view, auth=None),
            ],
            id="no_auth_root_not_set_auth_add",
        ),
        pytest.param(
            Router(
                operations=[Operation("/ping", "GET", some_view, auth=BearerAuth())],
                auth=BearerAuth(),
            ),
            Router(operations=[Operation("/ping", "GET", some_view)]),
            "/some_prefix",
            [
                Operation("/ping", "GET", some_view, auth=BearerAuth()),
                Operation("/some_prefix/ping", "GET", some_view, auth=BearerAuth()),
            ],
            id="bearer_auth_root_not_set_auth_add",
        ),
        pytest.param(
            Router(
                operations=[Operation("/ping", "GET", some_view, auth=BearerAuth())],
                auth=BearerAuth(),
            ),
            Router(
                operations=[Operation("/ping", "GET", some_view, auth=None)], auth=None
            ),
            "/some_prefix",
            [
                Operation("/ping", "GET", some_view, auth=BearerAuth()),
                Operation("/some_prefix/ping", "GET", some_view, auth=None),
            ],
            id="bearer_auth_root_no_auth_add",
        ),
    ],
)
def test_add_router(router, another_router, prefix, result_operations):
    router.add_router(another_router, prefix=prefix)

    assert len(router.operations) == len(result_operations)
    for operation, result_operation in zip(router.operations, result_operations):
        assert operation.path == result_operation.path
        assert operation.method == result_operation.method
        assert operation.auth == result_operation.auth
