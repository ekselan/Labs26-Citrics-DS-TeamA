import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.sql_query_function import fetch_query
from app.smart_upper_function import smart_upper
import pandas as pd
import plotly.express as px

router = APIRouter()


@router.get('/rent_viz_view/{cityname}_{statecode}')
async def viz(cityname: str, statecode: str):
    """
    Visualize city-level rental price estimates from
    [Apartment List](https://www.apartmentlist.com/research/category/data-rent-estimates) 📈

    ## Path Parameter
    `cityname`: The name of a U.S. city; e.g. `Atlanta` or `Los Angeles`
    - **Special Examples:**
        - **DC:** *Washington DC* should be entered as `Washington` or `washington`

    `statecode`: The [USPS 2 letter abbreviation](https://en.wikipedia.org/wiki/List_of_U.S._state_and_territory_abbreviations#Table)
    (case insensitive) for any of the 50 states or the District of Columbia.

    ## Response
    Plotly Express bar chart of `cityname`s rental price estimates
    """

    # Get the city's rental price from database
    query = """
    SELECT
        city,
        "state",
        bedroom_size,
        price_2020_08
    FROM rp_clean1
    """

    columns = ["city", "state", "bedroom_size", "price_2020_08"]

    df = pd.read_json(fetch_query(query, columns))

    # Input sanitization
    cityname = smart_upper(cityname)
    statecode = statecode.lower().upper()

    # Handle Edge Cases:
    ### saint
    if cityname[0:5] == "Saint":
        cityname = cityname.replace("Saint","St.")

    elif cityname[0:3] == "St ":
        cityname = cityname.replace("St","St.")

    ### fort
    elif cityname[0:3] == "Ft ":
        cityname = cityname.replace("Ft","Fort")

    elif cityname[0:3] == "Ft.":
        cityname = cityname.replace("Ft.","Fort")

    # Make a set of citynames in the rental price data
    citynames = set(df.city.to_list())
    statecodes = set(df.state.to_list())

    # Raise HTTPException for unknown inputs
    if cityname not in citynames:
        raise HTTPException(
            status_code=404,
            detail=f'City name "{cityname}" not found!'
        )

    if statecode not in statecodes:
        raise HTTPException(
            status_code=404,
            detail=f'State code "{statecode}" not found!'
        )

    # Get subset for cityname input
    subset = df[df.city == cityname]

    # Create visualization
    fig = px.bar(
        subset,
        x="price_2020_08",
        y="bedroom_size",
        title=f"Rental Price Estimates for {cityname}, {statecode}",
        orientation="h",
        template="ggplot2+xgridoff+ygridoff",
        color="price_2020_08",
        hover_data=["city", "state", "bedroom_size", "price_2020_08"],
        labels={
            "price_2020_08": "Rental Price Estimate",
            "bedroom_size": "Number of Bedrooms"
        },
        barmode="relative"
    )

    fig.update_layout(
        font=dict(
            family="trebuchet ms",
            color="darkslateblue",
            size=18
        ),
        autosize=False,
        width=500,
        height=500
    )

    img = fig.to_image(format="png")

    return StreamingResponse(io.BytesIO(img), media_type="image/png")