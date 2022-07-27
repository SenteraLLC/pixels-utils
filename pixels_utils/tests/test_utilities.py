from sure import expect

from pixels_utils.constants.sentinel2 import (
    ASSETS_MSI,
    ELEMENT84_L2A_SCENE_URL,
    EXPRESSION_NDVI,
    SENTINEL_2_L2A_COLLECTION,
)
from pixels_utils.tests.conftest import geojson_fixture, sceneid_fixture
from pixels_utils.utilities import _check_assets_expression, get_assets_expression_query


def test_utilities_check_assets_expression_none():
    _check_assets_expression.when.called_with(
        assets=None, expression=None
    ).should.throw(ValueError, "Either <assets> or <expression> must be passed")


def test_utilities_check_assets_expression_both():
    _check_assets_expression.when.called_with(
        assets=ASSETS_MSI, expression=EXPRESSION_NDVI
    ).should.throw(
        ValueError, "Both <assets> and <expression> are set, but only one is allowed."
    )


def test_utilities_check_assets_expression_assets():
    assets, expression = _check_assets_expression(assets=ASSETS_MSI, expression=None)
    expect(assets).to.equal(ASSETS_MSI)
    expect(expression).to.equal(None)


def test_utilities_check_assets_expression_expression():
    assets, expression = _check_assets_expression(
        assets=None, expression=EXPRESSION_NDVI
    )
    expect(assets).to.equal(None)
    expect(expression).to.equal(EXPRESSION_NDVI)


def test_get_assets_expression_query_none(sceneid_fixture):
    scene_url = ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid_fixture
    )
    get_assets_expression_query.when.called_with(
        scene_url, assets=None, expression=None
    ).should.throw(ValueError, "Either <assets> or <expression> must be passed.")


def test_get_assets_expression_query_both(sceneid_fixture):
    scene_url = ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid_fixture
    )
    get_assets_expression_query.when.called_with(
        scene_url, assets=ASSETS_MSI, expression=EXPRESSION_NDVI
    ).should.throw(
        ValueError, "Both <assets> and <expression> are set, but only one is allowed."
    )


def test_get_assets_expression_query_assets(sceneid_fixture):
    scene_url = ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid_fixture
    )
    query, asset_main = get_assets_expression_query(
        scene_url, assets=ASSETS_MSI, expression=None
    )
    scene_url.should.equal(
        "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TGS_20220419_0_L2A"
    )
    query.should.be.a("dict")
    list(query.keys()).should.equal(["url", "assets"])
    query["url"].should.be.a("str")
    query["url"].should.equal(scene_url)
    query["assets"].should.be.a("tuple")
    query["assets"].should.equal(ASSETS_MSI)
    asset_main.should.be.a("str")
    asset_main.should.equal(ASSETS_MSI[0])


def test_get_assets_expression_query_expression(sceneid_fixture):
    scene_url = ELEMENT84_L2A_SCENE_URL.format(
        collection=SENTINEL_2_L2A_COLLECTION, sceneid=sceneid_fixture
    )
    query, asset_main = get_assets_expression_query(
        scene_url, assets=None, expression=EXPRESSION_NDVI
    )
    scene_url.should.equal(
        "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TGS_20220419_0_L2A"
    )
    query.should.be.a("dict")
    list(query.keys()).should.equal(["url", "expression"])
    query["url"].should.be.a("str")
    query["url"].should.equal(scene_url)
    query["expression"].should.be.a("str")
    query["expression"].should.equal(EXPRESSION_NDVI)
    asset_main.should.be.none
