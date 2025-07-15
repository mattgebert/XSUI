from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    """The root home endpoint for the XSUI web application."""
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """Get an item by its ID."""
    return {"item_id": item_id}


# https://gist.github.com/rajesh-ae/70666702104aacb2d42e95504fcefba9
# from fastapi import FastAPI, Response
# import plotly.express as px
# from pydantic import BaseModel, JsonValue
# import json
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins="*",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class PlotlyJSONSchema(BaseModel):
#     data: JsonValue
#     layout: JsonValue

# @app.get("/plotly_data", response_model=PlotlyJSONSchema)
# async def plotly_data():
#     df = px.data.gapminder().query("continent == 'Oceania'")
#     fig = px.line(df, x='year', y='lifeExp', color='country', markers=True)
#     this_plot_data = fig.to_json(pretty=True, engine="json")
#     this_plot_data = json.loads(this_plot_data)
#     return PlotlyJSONSchema(data=this_plot_data["data"], layout=this_plot_data["layout"])
#     # return Response(content=this_plot_data, media_type="application/json")
