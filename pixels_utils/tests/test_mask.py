import sure

from pixels_utils.constants.sentinel2 import ASSETS_MSI, EXPRESSION_NDVI
from pixels_utils.mask import SCL, build_numexpr_scl_mask

_ = sure.version


class Test_Mask_Build_Numexpr_ASSETS_None_EXPRESSION_None:
    ASSETS = None
    EXPRESSION = None
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_scl_mask_none(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS, expression=self.EXPRESSION
        ).should.return_value(None)

    def test_scl_mask_wl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.return_value(None)

    def test_scl_mask_bl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.return_value(None)

    def test_scl_mask_wl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            mask_value=NODATA,
        ).should.return_value(None)

    def test_scl_mask_bl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            mask_value=NODATA,
        ).should.return_value(None)


class Test_Mask_Build_Numexpr_ASSETS_MSI_EXPRESSION_None:
    ASSETS = ASSETS_MSI
    EXPRESSION = None
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_scl_mask_none(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS, expression=self.EXPRESSION
        ).should.return_value(self.ASSETS)

    def test_scl_mask_wl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_bl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_wl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            mask_value=NODATA,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_bl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            mask_value=NODATA,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )


class Test_Mask_Build_Numexpr_ASSETS_NONE_EXPRESSION_NDVI:
    ASSETS = None
    EXPRESSION = EXPRESSION_NDVI
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_scl_mask_none(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS, expression=self.EXPRESSION
        ).should.return_value(self.EXPRESSION)

    def test_scl_mask_wl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.return_value(
            "where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), 0.0));"
        )

    def test_scl_mask_bl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.return_value(
            "where(SCL == 4, 0.0, where(SCL == 5, 0.0, (B08-B04)/(B08+B04)));"
        )

    def test_scl_mask_wl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            mask_value=NODATA,
        ).should.return_value(
            "where(SCL == 4, (B08-B04)/(B08+B04), where(SCL == 5, (B08-B04)/(B08+B04), {nodata}));".format(
                nodata=NODATA
            )
        )

    def test_scl_mask_bl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            mask_value=NODATA,
        ).should.return_value(
            "where(SCL == 4, {nodata}, where(SCL == 5, {nodata}, (B08-B04)/(B08+B04)));".format(
                nodata=NODATA
            )
        )


class Test_Mask_Build_Numexpr_ASSETS_MSI_EXPRESSION_NDVI:
    ASSETS = ASSETS_MSI
    EXPRESSION = EXPRESSION_NDVI
    MASK_SCL = [SCL.VEGETATION, SCL.BARE_SOIL]

    def test_scl_mask_none(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS, expression=self.EXPRESSION
        ).should.return_value(self.ASSETS)

    def test_scl_mask_wl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_bl(self):
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_wl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=True,
            mask_value=NODATA,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )

    def test_scl_mask_bl_nodata(self):
        NODATA = -1
        build_numexpr_scl_mask.when.called_with(
            assets=self.ASSETS,
            expression=self.EXPRESSION,
            mask_scl=self.MASK_SCL,
            whitelist=False,
            mask_value=NODATA,
        ).should.throw(
            NotImplementedError,
            "<assets> not yet implemented for mask.build_numexpr_scl_mask()",
        )
