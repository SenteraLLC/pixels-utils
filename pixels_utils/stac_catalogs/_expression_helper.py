from dataclasses import dataclass, make_dataclass
from functools import cached_property
from json import dumps as json_dumps
from typing import List

from spyndex import bands as spyndex_bands
from spyndex import indices as spyndex_indices
from spyndex.axioms import Bands, SpectralIndex


def bands_as_common_names(spyndex_object: SpectralIndex, spyndex_bands: Bands = spyndex_bands) -> List[str]:
    """
    Returns a list of common names for the bands in a spyndex SpectralIndex object.

    E.g., for NDVI, returns ['nir', 'red'] (rather than ['N', 'R']).

    Args:
        spyndex_object (SpectralIndex): Spyndex SpectralIndex object (e.g., spyndex_indices.NDVI).
        spyndex_bands (Bands, optional): Spyndex Bands object to extract common name from. Defaults to spyndex_bands.

    Returns:
        List[str]: Commmon band names used in the spyndex_object.
    """
    return [spyndex_bands[band].common_name if band in spyndex_bands else band for band in spyndex_object.bands]


def formula_as_common_names(spyndex_object: SpectralIndex, spyndex_bands: Bands = spyndex_bands) -> str:
    """
    Returns a formula with common names for the bands in a spyndex SpectralIndex object.

    E.g., for NDVI, returns '(nir-red)/(nir+red)' (rather than '(N-R)/(N+R)').

    Args:
        spyndex_object (SpectralIndex): Spyndex SpectralIndex object (e.g., spyndex_indices.NDVI).
        spyndex_bands (Bands, optional): Spyndex Bands object to extract common name from. Defaults to spyndex_bands.

    Returns:
        str: Formula with common band names.
    """
    formula = spyndex_object.formula
    for band in spyndex_object.bands:
        try:
            formula = formula.replace(band, spyndex_bands[band].common_name)
        except KeyError:
            pass
    return formula


@dataclass
class Expression:
    """
    A class for representing titiler assets and expressions from spyndex objects.

    Adapted from spyndex: https://github.com/awesome-spectral-indices/spyndex. See `spyndex_indices.NDVI.__dict__`
    for the full list of attributes that belong to the SpectralIndex object.

    Args:
        spyndex_object (SpectralIndex): A spyndex SpectralIndex object.
        assets_override (List[str], optional): A custom list of assets to override the spyndex assets. Defaults to None.
        expression_override (str, optional): A custom formula to override the spyndex formula. Defaults to None.
    """

    spyndex_object: SpectralIndex
    assets_override: List[str] = None
    expression_override: str = None

    def __post_init__(self):
        self.assets
        self.expression
        if self.assets_override is not None:
            del self.assets
            self.assets = self.assets_override
        if self.expression_override is not None:
            del self.expression
            self.expression = self.expression_override

    @cached_property
    def short_name(self):
        return self.spyndex_object.short_name

    @cached_property
    def long_name(self):
        return self.spyndex_object.long_name

    @cached_property
    def bands(self):
        return self.spyndex_object.bands

    @cached_property
    def application_domain(self):
        return self.spyndex_object.application_domain

    @cached_property
    def reference(self):
        return self.spyndex_object.reference

    @cached_property
    def formula(self):
        return self.spyndex_object.formula

    @cached_property
    def assets(self):
        return bands_as_common_names(self.spyndex_object, spyndex_bands)

    @cached_property
    def expression(self):
        return formula_as_common_names(self.spyndex_object, spyndex_bands)

    def to_json(self):
        return json_dumps(self.__dict__, default=lambda x: x.__dict__, ensure_ascii=False)


Expressions = make_dataclass("Expressions", [(spectral_index, Expression) for spectral_index in spyndex_indices])
