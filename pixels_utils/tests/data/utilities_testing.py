def calculate_valid_pix_pct(stats_ndvi):
    valid_pix_pct = (
        stats_ndvi["valid_pixels"]
        / (stats_ndvi["valid_pixels"] + stats_ndvi["masked_pixels"])
    ) * 100
    return valid_pix_pct
