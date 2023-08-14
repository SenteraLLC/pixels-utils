import sure

from pixels_utils.stac_catalogs.earthsearch.v1 import EarthSearchCollections, expression_from_collection
from pixels_utils.titiler.mask._mask import build_numexpr_mask_enum
from pixels_utils.titiler.mask.enum_classes import Sentinel2_SCL_Group

_ = sure.version


class Test_Mask_Build_Numexpr_EXPRESSION_None:
    EXPRESSION = None
    MASK_ENUM = Sentinel2_SCL_Group.ARABLE  # [Sentinel2_SCL.VEGETATION, Sentinel2_SCL.BARE_SOIL]

    def test_scl_mask_none(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION, mask_enum=self.MASK_ENUM
        ).should.have.raised(TypeError)

    def test_scl_mask_wl(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION, mask_enum=self.MASK_ENUM, mask_asset="scl", whitelist=True, mask_value=0
        ).should.have.raised(TypeError)

    def test_scl_mask_bl(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION,
            mask_enum=self.MASK_ENUM,
            mask_asset="scl",
            whitelist=False,
            mask_value=0,
        ).should.have.raised(TypeError)

    def test_scl_mask_wl_nodata(self):
        NODATA = -1
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION,
            mask_enum=self.MASK_ENUM,
            mask_asset="scl",
            whitelist=True,
            mask_value=NODATA,
        ).should.have.raised(TypeError)

    def test_scl_mask_bl_nodata(self):
        NODATA = -1
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION,
            mask_enum=self.MASK_ENUM,
            mask_asset="scl",
            whitelist=False,
            mask_value=NODATA,
        ).should.have.raised(TypeError)


class Test_Mask_Build_Numexpr_EXPRESSION_NDVI:
    EXPRESSION = expression_from_collection(
        collection=EarthSearchCollections.sentinel_2_l2a, spectral_index="NDVI"
    ).expression
    MASK_ENUM = Sentinel2_SCL_Group.ARABLE

    def test_mask_asset_scl_wl(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION, mask_enum=self.MASK_ENUM, mask_asset="scl", whitelist=True, mask_value=0
        ).should.return_value("where(scl==4,(nir-red)/(nir+red),where(scl==5,(nir-red)/(nir+red),0));")

    def test_mask_asset_maskasset_wl(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION, mask_enum=self.MASK_ENUM, mask_asset="maskasset", whitelist=True, mask_value=0
        ).should.return_value("where(maskasset==4,(nir-red)/(nir+red),where(maskasset==5,(nir-red)/(nir+red),0));")

    def test_mask_asset_scl_bl(self):
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION, mask_enum=self.MASK_ENUM, mask_asset="scl", whitelist=False, mask_value=0
        ).should.return_value("where(scl==4,0,where(scl==5,0,(nir-red)/(nir+red)));")

    def test_mask_asset_scl_wl_nodata(self):
        NODATA = -1
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION,
            mask_enum=self.MASK_ENUM,
            mask_asset="scl",
            whitelist=True,
            mask_value=NODATA,
        ).should.return_value(
            "where(scl==4,(nir-red)/(nir+red),where(scl==5,(nir-red)/(nir+red),{nodata}));".format(nodata=NODATA)
        )

    def test_mask_asset_scl_bl_nodata(self):
        NODATA = -1
        build_numexpr_mask_enum.when.called_with(
            expression=self.EXPRESSION,
            mask_enum=self.MASK_ENUM,
            mask_asset="scl",
            whitelist=False,
            mask_value=NODATA,
        ).should.return_value(
            "where(scl==4,{nodata},where(scl==5,{nodata},(nir-red)/(nir+red)));".format(nodata=NODATA)
        )
